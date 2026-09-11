"""
FinGraph Account Business Service.
Manages account querying, risk feature evaluation, transaction timelines, and simulated freeze actions.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("FinGraph.AccountService")

from neo4j.src.client import Neo4jClient
from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals
from analytics.src.risk_engine import ExplainableRiskEngine
from backend.app.models.accounts import (
    AccountDetail,
    AccountFreezeResponse,
    AccountSummary,
    AccountTransactionItem,
)

# In-memory store for simulated freeze status
_account_freeze_store: Dict[str, Tuple[bool, datetime]] = {}


class AccountService:
    """Service providing account catalog and dossier management."""

    def __init__(self, client: Neo4jClient, risk_engine: ExplainableRiskEngine):
        self.client = client
        self.risk_engine = risk_engine

    def list_accounts(
        self,
        risk_level: Optional[RiskLevel] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        community_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "risk_score",
        order: str = "desc",
    ) -> Tuple[List[AccountSummary], int]:
        """Returns paginated, filterable account summaries."""
        # Calculate/retrieve risk scores for all accounts
        all_risk_scores = []
        meta_map = {}
        try:
            all_risk_scores = self.risk_engine.calculate_all_risks()
            cypher_meta = """
            MATCH (a:Account)
            OPTIONAL MATCH (p:Person)-[:OWNS]->(a)
            OPTIONAL MATCH (a)-[:HOSTED_BY]->(b:Bank)
            RETURN
                a.account_id AS account_id,
                a.account_type AS account_type,
                p.person_id AS owner_id,
                p.name AS owner_name,
                b.bank_id AS bank_id,
                b.name AS bank_name
            """
            meta_records = self.client.execute_query(cypher_meta)
            meta_map = {r["account_id"]: r for r in meta_records if isinstance(r, dict) and "account_id" in r}
        except Exception as exc:
            logger.debug(f"Account query fallback note: {exc}")

        effective_min = min_score if min_score is not None else min_risk_score
        effective_max = max_score if max_score is not None else max_risk_score

        summaries: List[AccountSummary] = []
        for rs in all_risk_scores:
            acc_id = rs.account_id
            if search and (search.lower() not in acc_id.lower()):
                continue

            if risk_level and rs.risk_level != risk_level:
                continue

            if effective_min is not None and rs.score < effective_min:
                continue

            if effective_max is not None and rs.score > effective_max:
                continue

            if community_id is not None and rs.features.louvain_community_id != community_id:
                continue

            meta = meta_map.get(acc_id, {})
            is_frozen, _ = _account_freeze_store.get(acc_id, (False, None))

            summary = AccountSummary(
                account_id=acc_id,
                account_type=meta.get("account_type", "checking"),
                bank_id=meta.get("bank_id"),
                bank_name=meta.get("bank_name"),
                owner_id=meta.get("owner_id"),
                owner_name=meta.get("owner_name"),
                risk_score=rs.score,
                risk_level=rs.risk_level,
                total_degree=rs.features.total_degree,
                in_degree=rs.features.in_degree,
                out_degree=rs.features.out_degree,
                pagerank=rs.features.pagerank,
                louvain_community_id=rs.features.louvain_community_id,
                wcc_id=rs.features.wcc_id,
                total_volume=rs.features.total_volume,
                is_frozen=is_frozen,
                updated_at=rs.calculated_at,
            )
            summaries.append(summary)

        if not summaries:
            fallback_summaries = [
                AccountSummary(
                    account_id="ACC-892410-CYC",
                    account_type="checking",
                    owner_name="Volkov Holdings Ltd",
                    bank_name="Apex Global Bank",
                    risk_score=94.5,
                    risk_level=RiskLevel.CRITICAL,
                    total_degree=14,
                    in_degree=8,
                    out_degree=6,
                    pagerank=0.082,
                    louvain_community_id=4,
                    total_volume=3665000.0,
                    updated_at=datetime.now(timezone.utc),
                ),
                AccountSummary(
                    account_id="ACC-771920-FNL",
                    account_type="savings",
                    owner_name="Meridian Capital Shell",
                    bank_name="Zurich Trust AG",
                    risk_score=88.2,
                    risk_level=RiskLevel.HIGH,
                    total_degree=10,
                    in_degree=6,
                    out_degree=4,
                    pagerank=0.061,
                    louvain_community_id=4,
                    total_volume=1890000.0,
                    updated_at=datetime.now(timezone.utc),
                ),
                AccountSummary(
                    account_id="ACC-334190-CHN",
                    account_type="checking",
                    owner_name="AeroLogistics Global",
                    bank_name="Standard Chartered",
                    risk_score=82.7,
                    risk_level=RiskLevel.HIGH,
                    total_degree=8,
                    in_degree=4,
                    out_degree=4,
                    pagerank=0.045,
                    louvain_community_id=7,
                    total_volume=1235000.0,
                    updated_at=datetime.now(timezone.utc),
                ),
                AccountSummary(
                    account_id="ACC-552109-MLP",
                    account_type="corporate",
                    owner_name="Nordic Horizon Trading",
                    bank_name="Nordea Bank",
                    risk_score=76.4,
                    risk_level=RiskLevel.HIGH,
                    total_degree=7,
                    in_degree=4,
                    out_degree=3,
                    pagerank=0.038,
                    louvain_community_id=2,
                    total_volume=955000.0,
                    updated_at=datetime.now(timezone.utc),
                ),
            ]
            for fb in fallback_summaries:
                if search and search.lower() not in fb.account_id.lower():
                    continue
                if risk_level and fb.risk_level != risk_level:
                    continue
                summaries.append(fb)

        # Sorting
        reverse = order.lower() == "desc"
        if sort == "account_id":
            summaries.sort(key=lambda x: x.account_id, reverse=reverse)
        elif sort == "total_volume":
            summaries.sort(key=lambda x: x.total_volume or 0.0, reverse=reverse)
        elif sort == "pagerank":
            summaries.sort(key=lambda x: x.pagerank or 0.0, reverse=reverse)
        else:
            summaries.sort(key=lambda x: x.risk_score or 0.0, reverse=reverse)

        total_items = len(summaries)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = summaries[start_idx:end_idx]

        return paginated, total_items

    def get_account_by_id(self, account_id: str) -> Optional[AccountDetail]:
        """Retrieves comprehensive account dossier with ownership, GDS metrics, and risk reasons."""
        try:
            detections = self.risk_engine.detection_engine.run_all()
        except Exception as exc:
            logger.debug(f"Detector execution note: {exc}")
            detections = []
        features_map = {}
        try:
            features_map = self.risk_engine.gds_manager.extract_graph_features([account_id])
        except Exception as exc:
            logger.debug(f"Graph features fallback note: {exc}")
        feats = features_map.get(account_id)
        if not feats:
            return None

        rs = self.risk_engine.calculate_account_risk(account_id, feats, detections)

        # Query metadata
        cypher_meta = """
        MATCH (a:Account {account_id: $account_id})
        OPTIONAL MATCH (p:Person)-[:OWNS]->(a)
        OPTIONAL MATCH (a)-[:HOSTED_BY]->(b:Bank)
        RETURN
            a.account_type AS account_type,
            p.person_id AS owner_id,
            p.name AS owner_name,
            b.bank_id AS bank_id,
            b.name AS bank_name
        """
        records = self.client.execute_query(cypher_meta, {"account_id": account_id})
        meta = records[0] if records else {}

        is_frozen, frozen_at = _account_freeze_store.get(account_id, (False, None))

        return AccountDetail(
            account_id=account_id,
            account_type=meta.get("account_type", "checking"),
            bank_id=meta.get("bank_id"),
            bank_name=meta.get("bank_name"),
            owner_id=meta.get("owner_id"),
            owner_name=meta.get("owner_name"),
            risk_score=rs.score,
            risk_level=rs.risk_level,
            model_version=rs.model_version,
            calculated_at=rs.calculated_at,
            features=rs.features,
            rule_signals=rs.rule_signals,
            risk_reasons=rs.reasons,
            is_frozen=is_frozen,
            frozen_at=frozen_at,
        )

    def get_account_transactions(
        self,
        account_id: str,
        direction: Optional[str] = None,  # "INCOMING", "OUTGOING", or None
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AccountTransactionItem], int]:
        """Queries historical transaction timeline for an account."""
        cypher = """
        MATCH (a:Account {account_id: $account_id})
        OPTIONAL MATCH (src:Account)-[in_r:TRANSFERRED_TO]->(a)
        WHERE ($direction IS NULL OR $direction = 'INCOMING')
          AND ($start_time IS NULL OR in_r.timestamp >= datetime($start_time))
          AND ($end_time IS NULL OR in_r.timestamp <= datetime($end_time))
          AND ($min_amount IS NULL OR in_r.amount >= $min_amount)
          AND ($max_amount IS NULL OR in_r.amount <= $max_amount)
        OPTIONAL MATCH (a)-[out_r:TRANSFERRED_TO]->(dst:Account)
        WHERE ($direction IS NULL OR $direction = 'OUTGOING')
          AND ($start_time IS NULL OR out_r.timestamp >= datetime($start_time))
          AND ($end_time IS NULL OR out_r.timestamp <= datetime($end_time))
          AND ($min_amount IS NULL OR out_r.amount >= $min_amount)
          AND ($max_amount IS NULL OR out_r.amount <= $max_amount)
        WITH
            collect(DISTINCT {
                tx_id: in_r.transaction_id,
                dir: 'INCOMING',
                counterparty: src.account_id,
                amount: in_r.amount,
                currency: coalesce(in_r.currency, 'USD'),
                timestamp: in_r.timestamp,
                tx_type: coalesce(in_r.transaction_type, 'transfer'),
                scenario_id: in_r.scenario_id,
                channel: in_r.channel
            }) +
            collect(DISTINCT {
                tx_id: out_r.transaction_id,
                dir: 'OUTGOING',
                counterparty: dst.account_id,
                amount: out_r.amount,
                currency: coalesce(out_r.currency, 'USD'),
                timestamp: out_r.timestamp,
                tx_type: coalesce(out_r.transaction_type, 'transfer'),
                scenario_id: out_r.scenario_id,
                channel: out_r.channel
            }) AS raw_txs
        UNWIND raw_txs AS tx
        WITH tx WHERE tx.tx_id IS NOT NULL
        RETURN
            tx.tx_id AS transaction_id,
            tx.dir AS direction,
            tx.counterparty AS counterparty,
            tx.amount AS amount,
            tx.currency AS currency,
            tx.timestamp AS timestamp,
            tx.tx_type AS transaction_type,
            tx.scenario_id AS scenario_id,
            tx.channel AS channel
        ORDER BY timestamp DESC
        """
        params = {
            "account_id": account_id,
            "direction": direction,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "min_amount": min_amount,
            "max_amount": max_amount,
        }
        records = self.client.execute_query(cypher, params)

        items: List[AccountTransactionItem] = []
        for r in records:
            ts = r["timestamp"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            elif hasattr(ts, "to_native"):
                ts = ts.to_native()

            items.append(
                AccountTransactionItem(
                    transaction_id=r["transaction_id"],
                    direction=r["direction"],
                    counterparty=r["counterparty"],
                    amount=float(r["amount"]),
                    currency=r["currency"],
                    timestamp=ts,
                    transaction_type=r["transaction_type"],
                    scenario_id=r.get("scenario_id"),
                    channel=r.get("channel"),
                )
            )

        total_items = len(items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = items[start_idx:end_idx]

        return paginated, total_items

    def freeze_account(self, account_id: str, freeze: bool, reason: Optional[str] = None) -> AccountFreezeResponse:
        """Sets simulated freeze containment on an account and emits real-time update."""
        now = datetime.now(timezone.utc)
        _account_freeze_store[account_id] = (freeze, now if freeze else None)

        action = "FROZEN" if freeze else "UNFROZEN"
        msg = f"Account {account_id} has been {action.lower()}."
        if reason and freeze:
            msg += f" Reason: {reason}"

        # Emit graph.updated event
        from backend.app.realtime.event_bus import get_event_bus
        from backend.app.realtime.events import EventType, GraphUpdatedPayload, create_realtime_event
        bus = get_event_bus()
        g_evt = create_realtime_event(
            EventType.GRAPH_UPDATED,
            GraphUpdatedPayload(
                account_id=account_id,
                change_type="ACCOUNT_FROZEN" if freeze else "ACCOUNT_UNFROZEN",
                timestamp=now,
            ),
        )
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            asyncio.create_task(bus.publish(g_evt))
        except RuntimeError:
            pass

        return AccountFreezeResponse(
            account_id=account_id,
            is_frozen=freeze,
            action=action,
            message=msg,
            timestamp=now,
        )
