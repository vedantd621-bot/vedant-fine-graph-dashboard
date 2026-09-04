"""
FinGraph Network Evolution Engine.
Calculates snapshot diffs, activity velocity, trajectory classification,
and detects emerging suspicious networks.
"""
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Tuple

from backend.app.network_evolution.models import (
    EmergingNetwork,
    EvolutionTimeWindow,
    NetworkEvolutionSnapshot,
    NetworkMetricsSnapshot,
    NetworkVelocity,
    RiskTrajectory,
)
from analytics.src.models import RiskLevel

logger = logging.getLogger("FinGraph.NetworkEvolutionEngine")

WINDOW_HOURS = {
    EvolutionTimeWindow.FIVE_MINUTES: 5.0 / 60.0,
    EvolutionTimeWindow.ONE_HOUR: 1.0,
    EvolutionTimeWindow.SIX_HOURS: 6.0,
    EvolutionTimeWindow.TWENTY_FOUR_HOURS: 24.0,
    EvolutionTimeWindow.SEVEN_DAYS: 168.0,
    EvolutionTimeWindow.THIRTY_DAYS: 720.0,
}


class NetworkEvolutionEngine:
    """Computes bounded snapshot comparisons, activity velocity, and emerging networks."""

    def __init__(self):
        pass

    def calculate_velocity(
        self,
        current: NetworkMetricsSnapshot,
        previous: NetworkMetricsSnapshot,
        window: EvolutionTimeWindow,
    ) -> NetworkVelocity:
        """
        Calculates activity velocity normalized per hour:
        V = Delta Metric / Delta Hours (guarded against division by zero).
        """
        hours = max(WINDOW_HOURS.get(window, 1.0), 0.001)

        delta_tx = max(0, current.transaction_count - previous.transaction_count)
        delta_acc = max(0, current.new_accounts_count)
        delta_cpty = max(0, current.new_counterparties_count)
        delta_exp = current.financial_exposure - previous.financial_exposure
        delta_risk = current.network_risk - previous.network_risk

        return NetworkVelocity(
            tx_velocity_per_hour=round(delta_tx / hours, 2),
            account_velocity_per_hour=round(delta_acc / hours, 2),
            counterparty_velocity_per_hour=round(delta_cpty / hours, 2),
            exposure_velocity_per_hour=round(delta_exp / hours, 2),
            risk_growth_per_hour=round(delta_risk / hours, 2),
        )

    def classify_trajectory(
        self,
        current_risk: float,
        previous_risk: float,
        risk_delta: float,
    ) -> RiskTrajectory:
        """
        Deterministic Risk Trajectory Classification:
        - risk_delta <= -10.0 -> DECREASING
        - -10.0 < risk_delta < 10.0 -> STABLE
        - 10.0 <= risk_delta < 25.0 -> INCREASING
        - risk_delta >= 25.0 -> RAPIDLY_INCREASING
        """
        if risk_delta <= -10.0:
            return RiskTrajectory.DECREASING
        elif risk_delta >= 25.0:
            return RiskTrajectory.RAPIDLY_INCREASING
        elif risk_delta >= 10.0:
            return RiskTrajectory.INCREASING
        else:
            return RiskTrajectory.STABLE

    def build_evolution_snapshot(
        self,
        network_id: str,
        current: NetworkMetricsSnapshot,
        previous: Optional[NetworkMetricsSnapshot],
        window: EvolutionTimeWindow,
        new_entities: Optional[List[str]] = None,
        removed_entities: Optional[List[str]] = None,
        emerging_patterns: Optional[List[str]] = None,
    ) -> NetworkEvolutionSnapshot:
        """Builds a complete evolution snapshot diff across a bounded window."""
        if previous is None:
            # Baseline snapshot
            previous = NetworkMetricsSnapshot(
                node_count=max(1, current.node_count - 1),
                edge_count=max(0, current.edge_count - 1),
                transaction_count=max(0, current.transaction_count - 2),
                financial_exposure=max(0.0, current.financial_exposure * 0.8),
                average_risk=current.average_risk,
                network_risk=current.network_risk,
            )

        growth_rate = 0.0
        if previous.node_count > 0:
            growth_rate = round(((current.node_count - previous.node_count) / previous.node_count) * 100.0, 2)

        risk_delta = round(current.network_risk - previous.network_risk, 2)
        exposure_delta = round(current.financial_exposure - previous.financial_exposure, 2)

        velocity = self.calculate_velocity(current, previous, window)
        trajectory = self.classify_trajectory(current.network_risk, previous.network_risk, risk_delta)

        return NetworkEvolutionSnapshot(
            network_id=network_id,
            window=window,
            previous_snapshot=previous,
            current_snapshot=current,
            growth_rate=growth_rate,
            risk_delta=risk_delta,
            exposure_delta=exposure_delta,
            velocity=velocity,
            trajectory=trajectory,
            new_entities=new_entities or [],
            removed_entities=removed_entities or [],
            emerging_patterns=emerging_patterns or [],
        )

    def detect_emerging_networks(
        self,
        networks_data: List[Dict[str, Any]],
    ) -> List[EmergingNetwork]:
        """Detects newly emerging suspicious network clusters with explainable scoring."""
        emerging: List[EmergingNetwork] = []

        for net in networks_data:
            growth = net.get("growth_rate", 0.0)
            risk = net.get("risk_score", 50.0)
            velocity = net.get("tx_velocity", 0.0)
            exposure = net.get("exposure", 0.0)

            # Emergence Score Formulation: 0.35 * Growth + 0.35 * Risk + 0.20 * Velocity + 0.10 * ExposureScore
            norm_growth = min(100.0, max(0.0, growth * 2.0))
            norm_risk = min(100.0, max(0.0, risk))
            norm_vel = min(100.0, max(0.0, velocity * 10.0))
            norm_exp = min(100.0, (exposure / 50000.0) * 100.0)

            emergence_score = round(
                0.35 * norm_growth + 0.35 * norm_risk + 0.20 * norm_vel + 0.10 * norm_exp,
                1,
            )

            if emergence_score >= 45.0:
                signals = []
                if norm_growth > 40:
                    signals.append(f"Rapid node growth of {growth:.1f}%")
                if norm_vel > 30:
                    signals.append(f"High transaction burst rate of {velocity:.1f} tx/hr")
                if norm_risk > 60:
                    signals.append(f"Elevated baseline network risk ({risk:.1f}/100)")
                if exposure > 20000:
                    signals.append(f"Accelerating financial exposure (${exposure:,.0f})")

                risk_level = (
                    RiskLevel.CRITICAL if emergence_score >= 80.0
                    else RiskLevel.HIGH if emergence_score >= 65.0
                    else RiskLevel.MEDIUM
                )

                emerging.append(
                    EmergingNetwork(
                        network_id=net.get("network_id", f"EMG-{net.get('id', '01')}"),
                        name=net.get("name", "Emerging Syndicate Cluster"),
                        emergence_score=emergence_score,
                        confidence=0.88,
                        risk_level=risk_level,
                        growth_metrics={
                            "growth_rate": growth,
                            "tx_velocity": velocity,
                            "financial_exposure": exposure,
                        },
                        supporting_signals=signals,
                        explanation=f"Emerging network detected with {emergence_score}/100 intensity: {'; '.join(signals)}",
                    )
                )

        emerging.sort(key=lambda x: x.emergence_score, reverse=True)
        return emerging
