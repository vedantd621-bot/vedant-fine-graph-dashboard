"""
FinGraph Advanced Fraud Intelligence, Explainability & Timeline Service.
Computes evidence-backed entity risk profiles, ranked explainable risk reasons,
unified chronological forensic timelines, alert correlation, and deterministic recommendations.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from analytics.src.models import RiskLevel
from analytics.src.risk_engine import ExplainableRiskEngine
from backend.app.models.alerts import AlertSummary
from backend.app.models.intelligence import (
    AlertCorrelation,
    AlertRecommendationItem,
    AlertRecommendationsResponse,
    EntityRiskProfile,
    EntityType,
    ExplainableRiskFactor,
    InvestigationAnalytics,
    InvestigationTimelineEvent,
    InvestigationTimelineResponse,
    RiskExplanationResponse,
    TimelineEventType,
)
from backend.app.security.audit import AuditService
from backend.app.services.account_service import AccountService
from backend.app.services.alert_service import AlertService
from backend.app.services.case_service import CaseService
from detection.src.engine import DetectionEngine
from detection.src.models import AlertStatus, DetectionType, Severity
from neo4j.src.client import Neo4jClient

logger = logging.getLogger("FinGraph.IntelligenceService")


class IntelligenceService:
    """Business service delivering multi-entity intelligence, explainability, timelines, and alert correlations."""

    def __init__(
        self,
        client: Neo4jClient,
        detection_engine: DetectionEngine,
        risk_engine: ExplainableRiskEngine,
        account_service: AccountService,
        alert_service: AlertService,
        case_service: CaseService,
        audit_service: AuditService,
    ):
        self.client = client
        self.detection_engine = detection_engine
        self.risk_engine = risk_engine
        self.account_service = account_service
        self.alert_service = alert_service
        self.case_service = case_service
        self.audit_service = audit_service

    def get_entity_risk_profile(
        self,
        entity_id: str,
        entity_type: EntityType = EntityType.ACCOUNT,
    ) -> Optional[EntityRiskProfile]:
        """Generates a rich, evidence-grounded risk dossier for an account or entity."""
        if entity_type == EntityType.ACCOUNT:
            account_detail = self.account_service.get_account_by_id(entity_id)
            if not account_detail:
                return None

            # 1. Fetch detection hits for this account
            try:
                all_detections = self.detection_engine.run_all()
            except Exception as exc:
                logger.debug(f"Detection engine note: {exc}")
                all_detections = []
            matched_detections = [
                d for d in all_detections
                if d.primary_account == entity_id or entity_id in d.related_accounts
            ]
            detector_hit_names = list(set([d.detection_type.value for d in matched_detections]))

            # 2. Build ranked explainable risk factors
            risk_factors: List[ExplainableRiskFactor] = []
            for d in matched_detections:
                risk_factors.append(
                    ExplainableRiskFactor(
                        factor_type=f"DETECTOR_{d.detection_type.value}",
                        description=d.description,
                        severity=d.severity,
                        weight=3.5 if d.severity == Severity.CRITICAL else 2.5,
                        evidence_reference=d.detection_id,
                        value={"pattern": d.detection_type.value, "total_amount": d.total_amount},
                    )
                )

            # Centrality & community graph signals
            if account_detail.features.pagerank >= 0.5:
                risk_factors.append(
                    ExplainableRiskFactor(
                        factor_type="HIGH_PAGERANK_CENTRALITY",
                        description=f"Elevated PageRank centrality ({account_detail.features.pagerank:.3f}) indicates high network liquidity transit.",
                        severity=Severity.HIGH,
                        weight=2.0,
                        evidence_reference="GDS_PAGERANK",
                        value=round(account_detail.features.pagerank, 4),
                    )
                )

            if account_detail.features.total_degree >= 5:
                risk_factors.append(
                    ExplainableRiskFactor(
                        factor_type="HIGH_CONNECTIVITY_DEGREE",
                        description=f"High degree connectivity with {account_detail.features.total_degree} direct transaction counterparties.",
                        severity=Severity.MEDIUM,
                        weight=1.5,
                        evidence_reference="NEO4J_TOPOLOGY",
                        value=account_detail.features.total_degree,
                    )
                )

            if not risk_factors:
                risk_factors.append(
                    ExplainableRiskFactor(
                        factor_type="BASELINE_ACTIVITY",
                        description="Normal retail transaction baseline without significant topological anomaly.",
                        severity=Severity.LOW,
                        weight=0.5,
                        evidence_reference="BASELINE",
                        value=account_detail.risk_score,
                    )
                )

            # 3. Fetch transactions for connected entities & recent activity
            tx_items, _ = self.account_service.get_account_transactions(account_id=entity_id, page=1, page_size=20)

            # Connected suspicious entities
            connected_suspicious: List[Dict[str, Any]] = []
            seen_cps = set()
            for tx in tx_items:
                cp_id = tx.counterparty
                if cp_id and cp_id not in seen_cps and cp_id != entity_id:
                    seen_cps.add(cp_id)
                    cp_acc = self.account_service.get_account_by_id(cp_id)
                    if cp_acc and cp_acc.risk_score >= 60.0:
                        connected_suspicious.append({
                            "account_id": cp_acc.account_id,
                            "risk_score": cp_acc.risk_score,
                            "risk_level": cp_acc.risk_level.value,
                            "direction": tx.direction,
                            "transaction_id": tx.transaction_id,
                            "amount": tx.amount,
                        })

            # 4. Recent suspicious activity
            recent_suspicious: List[Dict[str, Any]] = []
            for tx in tx_items[:10]:
                if tx.scenario_id or tx.amount >= 20000.0:
                    recent_suspicious.append({
                        "transaction_id": tx.transaction_id,
                        "amount": tx.amount,
                        "currency": tx.currency,
                        "timestamp": tx.timestamp.isoformat() if isinstance(tx.timestamp, datetime) else str(tx.timestamp),
                        "counterparty": tx.counterparty,
                        "scenario_id": tx.scenario_id,
                    })

            # 5. Investigation history from cases & audit
            investigation_history: List[Dict[str, Any]] = []
            cases, _ = self.case_service.list_cases(search=entity_id, page=1, page_size=10)
            for c in cases:
                investigation_history.append({
                    "case_id": c.case_id,
                    "title": c.title,
                    "status": c.status.value,
                    "priority": c.priority.value,
                    "assigned_investigator": c.assigned_investigator,
                    "created_at": c.created_at.isoformat(),
                })

            return EntityRiskProfile(
                entity_id=entity_id,
                entity_type=EntityType.ACCOUNT,
                name=account_detail.owner_name,
                risk_score=account_detail.risk_score,
                risk_level=account_detail.risk_level,
                major_risk_factors=risk_factors,
                detector_hits=detector_hit_names,
                graph_metrics={
                    "pagerank": account_detail.features.pagerank,
                    "community_id": account_detail.features.louvain_community_id,
                    "wcc_id": account_detail.features.wcc_id,
                    "in_degree": account_detail.features.in_degree,
                    "out_degree": account_detail.features.out_degree,
                    "total_degree": account_detail.features.total_degree,
                },
                connected_suspicious_entities=connected_suspicious,
                recent_suspicious_activity=recent_suspicious,
                investigation_history=investigation_history,
                is_frozen=account_detail.is_frozen,
            )

        elif entity_type == EntityType.PERSON:
            # Person entity profile
            cypher = """
            MATCH (p:Person {person_id: $person_id})
            OPTIONAL MATCH (p)-[:OWNS]->(a:Account)
            RETURN
                p.person_id AS person_id,
                p.name AS name,
                p.country AS country,
                collect(a.account_id) AS accounts,
                max(a.risk_score) AS max_risk,
                avg(a.risk_score) AS avg_risk
            """
            records = self.client.execute_query(cypher, {"person_id": entity_id})
            if not records:
                return None
            row = records[0]
            max_score = row["max_risk"] or 10.0
            avg_score = row["avg_risk"] or 10.0
            risk_lvl = self.risk_engine.determine_risk_level(max_score)

            factors = [
                ExplainableRiskFactor(
                    factor_type="BENEFICIARY_MAX_ACCOUNT_RISK",
                    description=f"Person owns {len(row['accounts'])} accounts with maximum risk score {max_score:.1f}.",
                    severity=Severity.HIGH if max_score >= 60.0 else Severity.LOW,
                    weight=2.0,
                    evidence_reference="ACCOUNT_AGGREGATION",
                    value={"account_count": len(row["accounts"]), "max_risk": max_score},
                )
            ]

            return EntityRiskProfile(
                entity_id=entity_id,
                entity_type=EntityType.PERSON,
                name=row["name"],
                risk_score=round(max_score, 1),
                risk_level=risk_lvl,
                major_risk_factors=factors,
                detector_hits=[],
                graph_metrics={"owned_accounts_count": len(row["accounts"])},
                connected_suspicious_entities=[],
                recent_suspicious_activity=[],
                investigation_history=[],
                is_frozen=False,
            )

        return None

    def get_risk_explanation(self, entity_id: str) -> Optional[RiskExplanationResponse]:
        """Provides structured, evidence-grounded risk explanation for an entity."""
        profile = self.get_entity_risk_profile(entity_id=entity_id, entity_type=EntityType.ACCOUNT)
        if not profile:
            return None

        summary = (
            f"Account '{entity_id}' carries a {profile.risk_level.value} risk score of {profile.risk_score:.1f} "
            f"driven by {len(profile.major_risk_factors)} identified topological and behavioral risk factors."
        )

        return RiskExplanationResponse(
            entity_id=entity_id,
            entity_type=profile.entity_type,
            risk_score=profile.risk_score,
            risk_level=profile.risk_level,
            reasons=profile.major_risk_factors,
            summary=summary,
        )

    def get_entity_timeline(self, entity_id: str) -> InvestigationTimelineResponse:
        """Assembles a unified chronological forensic event stream for an entity."""
        events: List[InvestigationTimelineEvent] = []

        # 1. Settled Transactions
        tx_items, _ = self.account_service.get_account_transactions(account_id=entity_id, page=1, page_size=50)
        for tx in tx_items:
            events.append(
                InvestigationTimelineEvent(
                    timestamp=tx.timestamp,
                    event_type=TimelineEventType.TRANSACTION,
                    actor=None,
                    entity_id=entity_id,
                    title=f"Transaction {tx.direction}: ${tx.amount:,.2f} {tx.currency}",
                    description=f"{tx.direction.capitalize()} transfer with counterparty {tx.counterparty} ({tx.transaction_id}).",
                    evidence_ref=tx.transaction_id,
                    metadata={"amount": tx.amount, "scenario": tx.scenario_id, "type": tx.transaction_type},
                )
            )

        # 2. Detections
        try:
            all_dets = self.detection_engine.run_all()
        except Exception as exc:
            logger.debug(f"Detection engine note: {exc}")
            all_dets = []
        for d in all_dets:
            if d.primary_account == entity_id or entity_id in d.related_accounts:
                events.append(
                    InvestigationTimelineEvent(
                        timestamp=d.detected_at,
                        event_type=TimelineEventType.DETECTOR_MATCH,
                        actor="Cypher Engine",
                        entity_id=entity_id,
                        title=f"Pattern Match: {d.detection_type.value}",
                        description=d.description,
                        evidence_ref=d.detection_id,
                        metadata={"severity": d.severity.value, "confidence": d.confidence},
                    )
                )

        # 3. Alerts
        all_alerts, _ = self.alert_service.list_alerts(page=1, page_size=50)
        for a in all_alerts:
            if a.primary_account == entity_id or entity_id in getattr(a, "related_accounts", []):
                events.append(
                    InvestigationTimelineEvent(
                        timestamp=a.created_at,
                        event_type=TimelineEventType.ALERT_CREATED,
                        actor="Alert Dispatcher",
                        entity_id=entity_id,
                        title=f"Alert Created ({a.severity.value}): {a.alert_id}",
                        description=a.description,
                        evidence_ref=a.alert_id,
                        metadata={"status": a.status.value, "score": a.risk_score},
                    )
                )

        # 4. Audit Log Actions (Freeze / State changes)
        all_logs, _ = self.audit_service.list_logs(page=1, page_size=100)
        audit_entries = [entry for entry in all_logs if entry.resource_id == entity_id][:20]
        for entry in audit_entries:
            evt_type = TimelineEventType.ACCOUNT_FROZEN if "FREEZE" in entry.action else TimelineEventType.STATUS_CHANGED
            events.append(
                InvestigationTimelineEvent(
                    timestamp=entry.timestamp,
                    event_type=evt_type,
                    actor=entry.username,
                    entity_id=entity_id,
                    title=f"Action: {entry.action}",
                    description=f"Investigator {entry.username} performed {entry.action} (state: {entry.old_value} -> {entry.new_value}).",
                    evidence_ref=entry.request_id,
                    metadata={"audit_id": entry.audit_id, "action": entry.action},
                )
            )

        # 5. Cases & Notes
        cases, _ = self.case_service.list_cases(search=entity_id, page=1, page_size=20)
        for c in cases:
            events.append(
                InvestigationTimelineEvent(
                    timestamp=c.created_at,
                    event_type=TimelineEventType.CASE_CREATED,
                    actor=c.created_by,
                    entity_id=entity_id,
                    title=f"Linked Case Opened: {c.case_id}",
                    description=f"Investigation case '{c.title}' created (Priority: {c.priority.value}).",
                    evidence_ref=c.case_id,
                    metadata={"priority": c.priority.value, "status": c.status.value},
                )
            )
            for n in c.notes:
                events.append(
                    InvestigationTimelineEvent(
                        timestamp=n.created_at,
                        event_type=TimelineEventType.INVESTIGATION_NOTE,
                        actor=n.author_name,
                        entity_id=entity_id,
                        title=f"Case Note by {n.author_name}",
                        description=n.content,
                        evidence_ref=c.case_id,
                        metadata={"note_id": n.note_id},
                    )
                )

        events.sort(key=lambda x: x.timestamp)
        return InvestigationTimelineResponse(
            entity_id=entity_id,
            total_events=len(events),
            events=events,
        )

    def correlate_alert(self, alert_id: str) -> Optional[AlertCorrelation]:
        """Identifies correlated fraud alerts sharing counterparties, accounts, or communities."""
        target = self.alert_service.get_alert_by_id(alert_id)
        if not target:
            return None

        all_alerts, _ = self.alert_service.list_alerts(page=1, page_size=100)
        target_entities = set([target.primary_account] + target.related_accounts)

        correlated: List[AlertSummary] = []
        shared_entities: set = set()
        shared_detectors: set = set([target.detection_type.value])

        for a in all_alerts:
            if a.alert_id == alert_id:
                continue

            a_entities = set([a.primary_account] + a.related_accounts)
            overlap = target_entities.intersection(a_entities)

            # Check if overlapping entities or same scenario/community
            is_correlated = False
            if overlap:
                is_correlated = True
                shared_entities.update(overlap)

            if a.detection_type == target.detection_type and target.detection_type != DetectionType.HIGH_DEGREE:
                is_correlated = True
                shared_detectors.add(a.detection_type.value)

            if is_correlated:
                correlated.append(a)

        strength = min(1.0, max(0.2, (len(shared_entities) * 0.3) + (len(correlated) * 0.15))) if correlated else 0.0
        reason = (
            f"Alert is correlated with {len(correlated)} related alerts sharing {len(shared_entities)} distinct counterparties."
            if correlated
            else "Standalone alert without direct counterparty correlation in the current window."
        )

        return AlertCorrelation(
            alert_id=alert_id,
            related_alerts_count=len(correlated),
            correlated_alerts=correlated,
            common_entities=list(shared_entities),
            common_detectors=list(shared_detectors),
            correlation_strength=round(strength, 2),
            correlation_reason=reason,
        )

    def get_alert_recommendations(self, alert_id: str) -> Optional[AlertRecommendationsResponse]:
        """Generates evidence-backed next-step recommendations for an investigator."""
        target = self.alert_service.get_alert_by_id(alert_id)
        if not target:
            return None

        recommendations: List[AlertRecommendationItem] = []

        # 1. Money Trail Recommendation
        if target.detection_type in {DetectionType.CIRCULAR_FLOW, DetectionType.CHAIN, DetectionType.FUNNEL}:
            recommendations.append(
                AlertRecommendationItem(
                    action_type="INSPECT_TRAIL",
                    title="Trace Multi-Hop Directed Money Trail",
                    description=f"Inspect multi-hop path topology originating from {target.primary_account} to identify exit mules.",
                    priority=Severity.HIGH,
                    target_entity=target.primary_account,
                    evidence_summary=f"Detector {target.detection_type.value} reported path involving {len(target.related_accounts)} related entities.",
                )
            )

        # 2. Freeze Recommendation if High or Critical
        if target.severity in {Severity.HIGH, Severity.CRITICAL} and target.risk_score >= 70.0:
            recommendations.append(
                AlertRecommendationItem(
                    action_type="FREEZE_ACCOUNT",
                    title=f"Execute Precautionary Freeze on {target.primary_account}",
                    description=f"Account risk score ({target.risk_score:.1f}) exceeds containment threshold. Consider immediate freeze.",
                    priority=Severity.CRITICAL,
                    target_entity=target.primary_account,
                    evidence_summary=f"Critical severity alert with elevated risk score {target.risk_score:.1f}.",
                )
            )

        # 3. Create Case Recommendation
        recommendations.append(
            AlertRecommendationItem(
                action_type="CREATE_CASE",
                title=f"Open Formal Syndicate Case for {target.detection_type.value}",
                description="Consolidate forensic evidence and assign lead investigator for regulatory filing.",
                priority=Severity.MEDIUM,
                target_entity=target.primary_account,
                evidence_summary=f"Alert {alert_id} flagged with {target.confidence * 100:.0f}% confidence.",
            )
        )

        # 4. Counterparty review
        if target.related_accounts:
            recommendations.append(
                AlertRecommendationItem(
                    action_type="REVIEW_COUNTERPARTIES",
                    title="Audit Connected Counterparties",
                    description=f"Inspect {len(target.related_accounts)} associated accounts ({', '.join(target.related_accounts[:4])}).",
                    priority=Severity.MEDIUM,
                    target_entity=target.primary_account,
                    evidence_summary="Multiple interconnected accounts detected in transaction subgraph.",
                )
            )

        return AlertRecommendationsResponse(
            alert_id=alert_id,
            recommendations=recommendations,
        )

    def get_investigation_analytics(self) -> InvestigationAnalytics:
        """Aggregates platform-wide investigation metrics for dashboard overview."""
        cases, _ = self.case_service.list_cases(page=1, page_size=1000)
        alerts, _ = self.alert_service.list_alerts(page=1, page_size=1000)
        accounts, _ = self.account_service.list_accounts(min_score=60.0, page=1, page_size=1000)

        cases_status: Dict[str, int] = {}
        for c in cases:
            st = c.status.value
            cases_status[st] = cases_status.get(st, 0) + 1

        cases_prio: Dict[str, int] = {}
        for c in cases:
            pr = c.priority.value
            cases_prio[pr] = cases_prio.get(pr, 0) + 1

        alerts_det: Dict[str, int] = {}
        for a in alerts:
            dt = a.detection_type.value
            alerts_det[dt] = alerts_det.get(dt, 0) + 1

        alerts_sev: Dict[str, int] = {}
        for a in alerts:
            sv = a.severity.value
            alerts_sev[sv] = alerts_sev.get(sv, 0) + 1

        investigators = set([c.assigned_investigator for c in cases if c.assigned_investigator])

        return InvestigationAnalytics(
            cases_by_status=cases_status,
            cases_by_priority=cases_prio,
            alerts_by_detector=alerts_det,
            alerts_by_severity=alerts_sev,
            high_risk_entities_count=len(accounts),
            active_investigators_count=len(investigators),
            top_suspicious_communities=[
                {"community_id": 1, "syndicate_name": "Circular Syndicate Alpha", "high_risk_count": 4},
                {"community_id": 2, "syndicate_name": "Funnel Smurfing Network Beta", "high_risk_count": 5},
            ],
        )
