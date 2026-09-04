"""
FinGraph Alert Prioritization & SLA Engine Service.
Provides deterministic 4-factor operational priority scoring, SLA countdown calculations,
and explainable priority breakdowns for triage workstations.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("FinGraph.AlertPrioritizationService")

from detection.src.models import Alert, DetectionType, Severity
from analytics.src.models import RiskLevel
from backend.app.models.operations import (
    AlertPriorityExplanation,
    PrioritizedAlert,
    PriorityFactor,
    PriorityLevel,
    SLAItem,
    SLAStatus,
    TriageStatus,
)

# Configurable default SLA durations in minutes
DEFAULT_SLA_MINUTES = {
    PriorityLevel.P0_CRITICAL: 15,
    PriorityLevel.P1_HIGH: 60,
    PriorityLevel.P2_MEDIUM: 240,     # 4 hours
    PriorityLevel.P3_LOW: 1440,       # 24 hours
}


class AlertPrioritizationService:
    """Service providing deterministic priority scoring, SLA computation, and explainability."""

    def __init__(self, sla_config: Optional[Dict[PriorityLevel, int]] = None):
        self.sla_config = sla_config or DEFAULT_SLA_MINUTES

    def calculate_priority(
        self,
        alert_id: str,
        detection_type: DetectionType,
        severity: Severity,
        confidence: float,
        entity_risk_score: float,
        network_risk_score: Optional[float] = None,
        total_amount: Optional[float] = None,
        anomaly_score: Optional[float] = None,
        related_alerts_count: int = 0,
        triage_status: TriageStatus = TriageStatus.NEW,
    ) -> Tuple[float, PriorityLevel, List[PriorityFactor], str]:
        """
        Calculates a deterministic priority score (0-100) using 4 explainable signal weights:
        1. Entity Risk Signal (w = 0.30): Composite graph risk score of primary account.
        2. Network Risk Signal (w = 0.25): Discovered syndicate/community risk score.
        3. Severity & Impact Signal (w = 0.25): Alert severity level + transaction volume magnitude.
        4. Behavioral Anomaly & Velocity Signal (w = 0.20): Behavioral deviations + related alert volume.
        """
        factors: List[PriorityFactor] = []

        # 1. Entity Risk Factor (0-100)
        norm_entity_risk = min(100.0, max(0.0, float(entity_risk_score)))
        w_entity = 0.30
        c_entity = norm_entity_risk * w_entity
        factors.append(
            PriorityFactor(
                factor_name="Entity Graph Risk",
                weight=w_entity,
                raw_value=round(norm_entity_risk, 2),
                contribution=round(c_entity, 2),
                evidence=f"Primary account composite risk score is {norm_entity_risk:.1f}/100",
            )
        )

        # 2. Network Risk Factor (0-100)
        norm_net_risk = min(100.0, max(0.0, float(network_risk_score if network_risk_score is not None else (norm_entity_risk * 0.7))))
        w_net = 0.25
        c_net = norm_net_risk * w_net
        factors.append(
            PriorityFactor(
                factor_name="Syndicate Network Risk",
                weight=w_net,
                raw_value=round(norm_net_risk, 2),
                contribution=round(c_net, 2),
                evidence=f"Fraud network / community risk aggregation is {norm_net_risk:.1f}/100",
            )
        )

        # 3. Severity & Transaction Impact Factor (0-100)
        sev_weights = {
            Severity.CRITICAL: 100.0,
            Severity.HIGH: 75.0,
            Severity.MEDIUM: 50.0,
            Severity.LOW: 25.0,
        }
        base_sev = sev_weights.get(severity, 50.0)
        # Volume boost up to +20 points for >= $100k
        amt = total_amount or 0.0
        vol_boost = min(20.0, (amt / 100000.0) * 20.0)
        norm_sev_impact = min(100.0, (base_sev * 0.8) + vol_boost)
        w_sev = 0.25
        c_sev = norm_sev_impact * w_sev
        factors.append(
            PriorityFactor(
                factor_name="Severity & Financial Impact",
                weight=w_sev,
                raw_value=round(norm_sev_impact, 2),
                contribution=round(c_sev, 2),
                evidence=f"{severity.value} severity with ${amt:,.2f} total transaction exposure",
            )
        )

        # 4. Behavioral Anomaly & Velocity Signal (0-100)
        anomaly_val = min(100.0, max(0.0, float(anomaly_score or 0.0)))
        alert_velocity_boost = min(30.0, related_alerts_count * 10.0)
        norm_anomaly_velocity = min(100.0, (anomaly_val * 0.7) + alert_velocity_boost)
        w_anom = 0.20
        c_anom = norm_anomaly_velocity * w_anom
        factors.append(
            PriorityFactor(
                factor_name="Behavioral Anomaly & Velocity",
                weight=w_anom,
                raw_value=round(norm_anomaly_velocity, 2),
                contribution=round(c_anom, 2),
                evidence=f"Anomaly score {anomaly_val:.1f} with {related_alerts_count} related detection alerts",
            )
        )

        total_score = round(sum(f.contribution for f in factors), 2)
        total_score = min(100.0, max(0.0, total_score))

        # Determine Priority Tier
        if total_score >= 80.0:
            tier = PriorityLevel.P0_CRITICAL
        elif total_score >= 60.0:
            tier = PriorityLevel.P1_HIGH
        elif total_score >= 35.0:
            tier = PriorityLevel.P2_MEDIUM
        else:
            tier = PriorityLevel.P3_LOW

        summary = (
            f"Alert {alert_id} assigned {tier.value} priority (Score: {total_score:.1f}/100) "
            f"based on {norm_entity_risk:.1f} entity risk and {severity.value} severity."
        )

        return total_score, tier, factors, summary

    def calculate_sla(
        self,
        priority_level: PriorityLevel,
        created_at: datetime,
        triage_status: TriageStatus,
        now: Optional[datetime] = None,
    ) -> Tuple[datetime, SLAStatus, float]:
        """
        Calculates SLA deadline, status, and remaining minutes.
        """
        current_time = now or datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        sla_minutes = self.sla_config.get(priority_level, 240)
        deadline = created_at + timedelta(minutes=sla_minutes)

        # If already resolved/closed/false_positive, mark as RESOLVED
        if triage_status in {TriageStatus.CONFIRMED_FRAUD, TriageStatus.FALSE_POSITIVE, TriageStatus.CLOSED}:
            time_remaining = max(0.0, (deadline - current_time).total_seconds() / 60.0)
            return deadline, SLAStatus.RESOLVED, round(time_remaining, 1)

        delta_seconds = (deadline - current_time).total_seconds()
        time_remaining_min = delta_seconds / 60.0

        if delta_seconds <= 0:
            return deadline, SLAStatus.BREACHED, 0.0

        # At risk if less than 25% of SLA threshold remains
        if time_remaining_min <= (sla_minutes * 0.25):
            return deadline, SLAStatus.AT_RISK, round(time_remaining_min, 1)

        return deadline, SLAStatus.WITHIN_SLA, round(time_remaining_min, 1)

    def explain_priority(
        self,
        alert_id: str,
        detection_type: DetectionType,
        severity: Severity,
        confidence: float,
        entity_risk_score: float,
        network_risk_score: Optional[float] = None,
        total_amount: Optional[float] = None,
        anomaly_score: Optional[float] = None,
        related_alerts_count: int = 0,
    ) -> AlertPriorityExplanation:
        """Returns structured explanation of the priority score."""
        score, tier, factors, summary = self.calculate_priority(
            alert_id=alert_id,
            detection_type=detection_type,
            severity=severity,
            confidence=confidence,
            entity_risk_score=entity_risk_score,
            network_risk_score=network_risk_score,
            total_amount=total_amount,
            anomaly_score=anomaly_score,
            related_alerts_count=related_alerts_count,
        )
        return AlertPriorityExplanation(
            alert_id=alert_id,
            priority_score=score,
            priority_level=tier,
            factors=factors,
            summary=summary,
        )
