"""
FinGraph Alert Business Service.
Manages alert generation, filtering, forensic detail retrieval, and investigation lifecycle transitions.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from neo4j.src.client import Neo4jClient
from detection.src.engine import DetectionEngine
from detection.src.models import Alert, AlertStatus, DetectionType, Severity
from analytics.src.models import RiskLevel
from analytics.src.risk_engine import ExplainableRiskEngine
from backend.app.models.alerts import AlertDetail, AlertSummary

# In-memory alert status override store to preserve analyst status updates across runs
_alert_status_store: Dict[str, Tuple[AlertStatus, datetime]] = {}


class AlertService:
    """Service providing alert query and state management operations."""

    def __init__(
        self,
        client: Neo4jClient,
        detection_engine: DetectionEngine,
        risk_engine: ExplainableRiskEngine,
    ):
        self.client = client
        self.detection_engine = detection_engine
        self.risk_engine = risk_engine

    def list_alerts(
        self,
        severity: Optional[Severity] = None,
        status: Optional[AlertStatus] = None,
        detection_type: Optional[DetectionType] = None,
        risk_level: Optional[RiskLevel] = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "created_at",
        order: str = "desc",
    ) -> Tuple[List[AlertSummary], int]:
        """Returns paginated, filterable list of active fraud alerts."""
        detections = self.detection_engine.run_all()
        generated_alerts = self.detection_engine.generate_alerts(detections)

        # Preload risk scores for primary accounts
        primary_accs = list(set(a.primary_account for a in generated_alerts))
        features_map = self.risk_engine.gds_manager.extract_graph_features(primary_accs)

        summaries: List[AlertSummary] = []
        for alt in generated_alerts:
            # Apply status overrides from investigator actions
            cur_status = _alert_status_store.get(alt.alert_id, (alt.status, alt.created_at))[0]
            if status and cur_status != status:
                continue

            if severity and alt.severity != severity:
                continue

            if detection_type and alt.detection_type != detection_type:
                continue

            # Compute or lookup primary account risk score
            acc_feats = features_map.get(alt.primary_account)
            r_score_val = 0.0
            r_level_val = RiskLevel.LOW
            if acc_feats:
                r_calc = self.risk_engine.calculate_account_risk(alt.primary_account, acc_feats, detections)
                r_score_val = r_calc.score
                r_level_val = r_calc.risk_level

            if risk_level and r_level_val != risk_level:
                continue

            summary = AlertSummary(
                alert_id=alt.alert_id,
                detection_type=alt.detection_type,
                severity=alt.severity,
                confidence=alt.confidence,
                primary_account=alt.primary_account,
                risk_score=r_score_val,
                risk_level=r_level_val,
                created_at=alt.created_at,
                status=cur_status,
                description=alt.description,
                total_amount=alt.total_amount,
                currency=alt.currency,
            )
            summaries.append(summary)

        # Sorting
        reverse = order.lower() == "desc"
        if sort == "risk_score":
            summaries.sort(key=lambda x: x.risk_score or 0.0, reverse=reverse)
        elif sort == "severity":
            severity_order = {Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3, Severity.CRITICAL: 4}
            summaries.sort(key=lambda x: severity_order.get(x.severity, 0), reverse=reverse)
        else:
            summaries.sort(key=lambda x: x.created_at, reverse=reverse)

        total_items = len(summaries)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = summaries[start_idx:end_idx]

        return paginated, total_items

    def get_alert_by_id(self, alert_id: str) -> Optional[AlertDetail]:
        """Retrieves comprehensive alert detail with evidence and reasons."""
        detections = self.detection_engine.run_all()
        generated_alerts = self.detection_engine.generate_alerts(detections)

        target_alert = next((a for a in generated_alerts if a.alert_id == alert_id), None)
        if not target_alert:
            return None

        status_override, updated_at = _alert_status_store.get(
            alert_id, (target_alert.status, target_alert.created_at)
        )

        # Risk calculation for account
        feats_map = self.risk_engine.gds_manager.extract_graph_features([target_alert.primary_account])
        acc_feats = feats_map.get(target_alert.primary_account)
        r_score = 0.0
        r_level = RiskLevel.LOW
        reasons = []

        if acc_feats:
            r_calc = self.risk_engine.calculate_account_risk(target_alert.primary_account, acc_feats, detections)
            r_score = r_calc.score
            r_level = r_calc.risk_level
            reasons = r_calc.reasons

        return AlertDetail(
            alert_id=target_alert.alert_id,
            detection_type=target_alert.detection_type,
            severity=target_alert.severity,
            confidence=target_alert.confidence,
            primary_account=target_alert.primary_account,
            risk_score=r_score,
            risk_level=r_level,
            created_at=target_alert.created_at,
            updated_at=updated_at,
            status=status_override,
            description=target_alert.description,
            evidence=target_alert.evidence,
            related_accounts=target_alert.related_accounts,
            transaction_ids=target_alert.transaction_ids,
            total_amount=target_alert.total_amount,
            currency=target_alert.currency,
            reasons=reasons,
        )

    def update_alert_status(self, alert_id: str, new_status: AlertStatus) -> Optional[AlertDetail]:
        """Updates the investigative lifecycle status for an alert."""
        detail = self.get_alert_by_id(alert_id)
        if not detail:
            return None

        now = datetime.now(timezone.utc)
        _alert_status_store[alert_id] = (new_status, now)

        return self.get_alert_by_id(alert_id)
