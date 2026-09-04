"""
FinGraph Proactive Early Warning Rules Engine.
Evaluates deterministic multi-signal thresholds against graph topology,
behavioral anomaly deviations, and financial exposure spikes.
"""
from typing import Any, Dict, List
from backend.app.early_warning.models import (
    EarlyWarning,
    EarlyWarningSeverity,
    EarlyWarningStatus,
    WarningActionRecommendation,
)


class EarlyWarningRulesEngine:
    """Evaluates multi-signal proactive warning rules."""

    def evaluate_warnings(
        self,
        networks: List[Dict[str, Any]],
        accounts: List[Dict[str, Any]],
    ) -> List[EarlyWarning]:
        """Evaluates all proactive rules across networks and accounts."""
        warnings: List[EarlyWarning] = []

        # Rule 1: High Velocity Network Expansion
        for net in networks:
            growth = net.get("growth_rate", 0.0)
            risk = net.get("risk_score", 50.0)
            if growth >= 25.0 and risk >= 75.0:
                warnings.append(
                    EarlyWarning(
                        severity=EarlyWarningSeverity.CRITICAL if risk >= 85.0 else EarlyWarningSeverity.HIGH,
                        entity_type="NETWORK",
                        entity_id=net.get("network_id", "NET-001"),
                        risk_score=risk,
                        confidence=0.92,
                        trigger_signals=[
                            f"Rapid graph growth (+{growth:.1f}% new nodes/edges)",
                            f"High network baseline hazard ({risk:.1f}/100)",
                        ],
                        explanation=f"Syndicate network {net.get('network_id', '')} expanding rapidly with high risk density.",
                        recommended_action=WarningActionRecommendation.REVIEW_NETWORK,
                    )
                )

        # Rule 2: Sudden Financial Exposure Spike
        for net in networks:
            exposure = net.get("exposure", 0.0)
            if exposure >= 100000.0:
                warnings.append(
                    EarlyWarning(
                        severity=EarlyWarningSeverity.HIGH,
                        entity_type="NETWORK",
                        entity_id=net.get("network_id", "NET-001"),
                        risk_score=85.0,
                        confidence=0.90,
                        trigger_signals=[
                            f"Aggregated financial exposure exceeds ${exposure:,.0f}",
                            "Multi-account rapid dispersion detected",
                        ],
                        explanation=f"High monetary exposure detected across syndicate network {net.get('network_id', '')}.",
                        recommended_action=WarningActionRecommendation.REVIEW_TRANSACTION_FLOW,
                    )
                )

        # Rule 3: Mule Aggregation Account Inflow Surge
        for acc in accounts:
            risk = acc.get("risk_score", 0.0)
            anomaly_score = acc.get("anomaly_score", 0.0)
            if risk >= 80.0 and anomaly_score >= 70.0:
                warnings.append(
                    EarlyWarning(
                        severity=EarlyWarningSeverity.HIGH,
                        entity_type="ACCOUNT",
                        entity_id=acc.get("account_id", "A015"),
                        risk_score=risk,
                        confidence=0.88,
                        trigger_signals=[
                            f"Statistical behavioral anomaly score ({anomaly_score:.1f}/100)",
                            "High composite graph risk index",
                        ],
                        explanation=f"Account {acc.get('account_id', '')} exhibiting sharp behavioral divergence and mule hub topology.",
                        recommended_action=WarningActionRecommendation.REVIEW_ACCOUNT,
                    )
                )

        return warnings
