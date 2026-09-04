"""
FinGraph Deterministic Investigation Priority Engine.
Calculates transparent 0-100 investigation priority scores combining risk, exposure, SLA, and contagion.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.intelligence_orchestration.models import (
    InvestigationPriorityScore,
    PriorityBand,
    PriorityFactor,
)


class InvestigationPriorityEngine:
    """
    Calculates deterministic investigation priority score from multi-source risk signals.
    PriorityScore = 0.25*Risk + 0.20*Exposure + 0.15*Severity + 0.15*SLA + 0.15*Contagion + 0.10*Campaign
    """

    def calculate_priority(
        self,
        risk_score: float = 85.0,
        financial_exposure: float = 125000.0,
        alert_severity: str = "CRITICAL",
        sla_hours_remaining: float = 2.5,
        threat_propagation_score: float = 82.0,
        has_active_campaign: bool = True,
    ) -> InvestigationPriorityScore:
        """
        Computes explainable investigation priority score and constituent factor breakdown.
        """
        # 1. Risk Factor (0.25)
        f_risk_val = min(100.0, max(0.0, risk_score))
        f_risk = PriorityFactor(
            name="Risk Score Index",
            weight=0.25,
            raw_value=f_risk_val,
            weighted_score=round(0.25 * f_risk_val, 2),
            description=f"Multi-factor entity hazard score ({f_risk_val:.1f}/100)",
        )

        # 2. Exposure Factor (0.20)
        f_exp_val = min(100.0, (financial_exposure / 150000.0) * 100.0)
        f_exp = PriorityFactor(
            name="Financial Exposure Volume",
            weight=0.20,
            raw_value=round(f_exp_val, 1),
            weighted_score=round(0.20 * f_exp_val, 2),
            description=f"Cumulative financial exposure (${financial_exposure:,.2f})",
        )

        # 3. Severity Factor (0.15)
        sev_map = {"CRITICAL": 100.0, "HIGH": 75.0, "MEDIUM": 50.0, "LOW": 25.0}
        f_sev_val = sev_map.get(alert_severity.upper(), 50.0)
        f_sev = PriorityFactor(
            name="Detection Severity Level",
            weight=0.15,
            raw_value=f_sev_val,
            weighted_score=round(0.15 * f_sev_val, 2),
            description=f"Alert rule classification ({alert_severity})",
        )

        # 4. SLA Urgency Factor (0.15)
        f_sla_val = min(100.0, max(0.0, (24.0 - sla_hours_remaining) / 24.0 * 100.0))
        f_sla = PriorityFactor(
            name="SLA Triage Urgency",
            weight=0.15,
            raw_value=round(f_sla_val, 1),
            weighted_score=round(0.15 * f_sla_val, 2),
            description=f"Time remaining until triage breach ({sla_hours_remaining:.1f}h remaining)",
        )

        # 5. Threat Contagion Factor (0.15)
        f_prop_val = min(100.0, max(0.0, threat_propagation_score))
        f_prop = PriorityFactor(
            name="Multi-Hop Contagion Spread",
            weight=0.15,
            raw_value=f_prop_val,
            weighted_score=round(0.15 * f_prop_val, 2),
            description=f"Threat propagation expansion index ({f_prop_val:.1f}/100)",
        )

        # 6. Campaign Association Factor (0.10)
        f_camp_val = 100.0 if has_active_campaign else 0.0
        f_camp = PriorityFactor(
            name="Coordinated Campaign Linkage",
            weight=0.10,
            raw_value=f_camp_val,
            weighted_score=round(0.10 * f_camp_val, 2),
            description="Linked to confirmed multi-case fraud campaign" if has_active_campaign else "Isolated entity",
        )

        factors = [f_risk, f_exp, f_sev, f_sla, f_prop, f_camp]
        total_score = round(sum(f.weighted_score for f in factors), 1)
        total_score = min(100.0, max(0.0, total_score))

        band = (
            PriorityBand.CRITICAL if total_score >= 80.0
            else PriorityBand.HIGH if total_score >= 60.0
            else PriorityBand.MEDIUM if total_score >= 40.0
            else PriorityBand.LOW
        )

        explanation = (
            f"Investigation priority assessed as {band.value} (Score: {total_score}/100) driven primarily by "
            f"elevated risk score ({f_risk_val:.1f}), ${financial_exposure:,.2f} exposed volume, and active campaign coordination."
        )

        return InvestigationPriorityScore(
            priority_score=total_score,
            priority_band=band,
            factors=factors,
            explanation=explanation,
        )
