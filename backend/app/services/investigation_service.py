"""
FinGraph Forensic Investigation Business Service.
Provides money trail path discovery, cross-entity search, and detection evidence inspection.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from neo4j.src.client import Neo4jClient
from detection.src.detectors.money_trail import MoneyTrailInvestigator
from detection.src.engine import DetectionEngine
from backend.app.models.accounts import AccountSummary
from backend.app.models.alerts import AlertSummary
from backend.app.models.investigation import (
    MoneyTrailPath,
    MoneyTrailStep,
    SearchResults,
)
from backend.app.services.account_service import AccountService
from backend.app.services.alert_service import AlertService


class InvestigationService:
    """Service providing forensic money trail tracing and multi-entity searching."""

    def __init__(
        self,
        client: Neo4jClient,
        detection_engine: DetectionEngine,
        account_service: AccountService,
        alert_service: AlertService,
    ):
        self.client = client
        self.detection_engine = detection_engine
        self.account_service = account_service
        self.alert_service = alert_service
        self.trail_investigator = MoneyTrailInvestigator(client=self.client)

    def trace_money_trail(
        self,
        from_account: str,
        to_account: Optional[str] = None,
        max_depth: int = 4,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[MoneyTrailPath]:
        """Traces multi-hop directed paths between accounts."""
        safe_depth = max(1, min(6, max_depth))
        raw_results = self.trail_investigator.trace(
            from_account=from_account,
            to_account=to_account,
            max_hops=safe_depth,
            start_time=start_time,
            end_time=end_time,
        )

        paths: List[MoneyTrailPath] = []
        for idx, res in enumerate(raw_results, 1):
            nodes = res.evidence.path_nodes
            steps: List[MoneyTrailStep] = []

            # Match individual steps
            for i in range(len(nodes) - 1):
                u, v = nodes[i], nodes[i + 1]
                steps.append(
                    MoneyTrailStep(
                        from_account=u,
                        to_account=v,
                        transaction_id=res.transaction_ids[i] if i < len(res.transaction_ids) else f"TX_HOP_{i+1}",
                        amount=res.total_amount or 0.0,
                        currency=res.currency,
                        timestamp=res.detected_at,
                        scenario_id=res.scenario_id,
                    )
                )

            path = MoneyTrailPath(
                path_id=f"PATH_{res.detection_id}",
                origin=nodes[0],
                destination=nodes[-1],
                hop_count=len(nodes) - 1,
                total_amount=res.total_amount or 0.0,
                path_nodes=nodes,
                steps=steps,
            )
            paths.append(path)

        return paths

    def search_entities(self, query: str) -> SearchResults:
        """Searches across accounts, transactions, and alerts for matches."""
        q = query.strip()
        if not q:
            return SearchResults(query=query)

        # 1. Accounts
        matched_accounts, _ = self.account_service.list_accounts(search=q, page=1, page_size=20)

        # 2. Alerts
        all_alerts, _ = self.alert_service.list_alerts(page=1, page_size=100)
        matched_alerts = [
            a for a in all_alerts if (q.lower() in a.alert_id.lower() or q.lower() in a.primary_account.lower() or q.lower() in a.description.lower())
        ]

        # 3. Transactions
        cypher_tx = """
        MATCH ()-[r:TRANSFERRED_TO]->()
        WHERE r.transaction_id CONTAINS $query OR r.scenario_id CONTAINS $query
        RETURN DISTINCT r.transaction_id AS tx_id
        LIMIT 20
        """
        records = self.client.execute_query(cypher_tx, {"query": q})
        tx_ids = [r["tx_id"] for r in records]

        return SearchResults(
            query=query,
            accounts=matched_accounts,
            alerts=matched_alerts,
            transaction_ids=tx_ids,
        )

    def get_detection_evidence(self, detection_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves raw explainable detection object by ID."""
        detections = self.detection_engine.run_all()
        target = next((d for d in detections if d.detection_id == detection_id), None)
        if not target:
            return None
        return target.model_dump(mode="json")
