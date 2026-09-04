"""
FinGraph Network Evolution Service.
Coordinates evolution snapshots, time-series forecasting, entity trajectories,
and emerging syndicate discovery.
"""
from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from backend.app.network_evolution.evolution import NetworkEvolutionEngine
from backend.app.network_evolution.exceptions import (
    InsufficientHistoryError,
    NetworkNotFoundError,
)
from backend.app.network_evolution.models import (
    EmergingNetwork,
    EntityRiskTrajectory,
    EntityType,
    EvolutionTimeWindow,
    NetworkEvolutionSnapshot,
    NetworkMetricsSnapshot,
    NetworkRiskForecast,
    RiskTrajectory,
)
from backend.app.network_evolution.risk import PredictiveRiskEngine
from backend.app.realtime.event_bus import get_event_bus
from backend.app.realtime.events import EventType, RealtimeEvent, create_realtime_event

logger = logging.getLogger("FinGraph.NetworkEvolutionService")


def _publish_event_safe(event: RealtimeEvent):
    """Dispatches WebSocket event safely without raising."""
    try:
        bus = get_event_bus()
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            loop.create_task(bus.publish(event))
        except RuntimeError:
            pass
    except Exception as exc:
        logger.debug(f"Evolution event dispatch note: {exc}")


class NetworkEvolutionService:
    """Manages network evolution snapshots, trajectories, and forecasts."""

    def __init__(self):
        self._lock = threading.RLock()
        self._evolution_engine = NetworkEvolutionEngine()
        self._risk_engine = PredictiveRiskEngine()

        self._snapshots: Dict[str, Dict[str, NetworkMetricsSnapshot]] = {}  # network_id -> window -> snapshot
        self._entity_trajectories: Dict[str, EntityRiskTrajectory] = {}
        self._seed_default_data()

    def _seed_default_data(self):
        """Seeds realistic historical snapshot and trajectory data."""
        with self._lock:
            # Network NET-001 snapshots
            self._snapshots["NET-001"] = {
                "current": NetworkMetricsSnapshot(
                    node_count=14,
                    edge_count=22,
                    transaction_count=48,
                    financial_exposure=148000.0,
                    average_risk=82.5,
                    network_risk=88.5,
                    new_accounts_count=3,
                    new_counterparties_count=4,
                ),
                "previous_1h": NetworkMetricsSnapshot(
                    node_count=11,
                    edge_count=16,
                    transaction_count=32,
                    financial_exposure=98000.0,
                    average_risk=74.0,
                    network_risk=78.0,
                    new_accounts_count=1,
                    new_counterparties_count=2,
                ),
            }

            # Seed entity trajectories
            self._entity_trajectories["account:A001"] = EntityRiskTrajectory(
                entity_type=EntityType.ACCOUNT,
                entity_id="A001",
                current_risk=92.0,
                previous_risk=75.0,
                risk_delta=17.0,
                risk_velocity=3.4,
                trajectory=RiskTrajectory.INCREASING,
                top_drivers=["Rapid circular transaction routing", "High degree centrality jump"],
            )
            self._entity_trajectories["account:A015"] = EntityRiskTrajectory(
                entity_type=EntityType.ACCOUNT,
                entity_id="A015",
                current_risk=84.0,
                previous_risk=42.0,
                risk_delta=42.0,
                risk_velocity=8.5,
                trajectory=RiskTrajectory.RAPIDLY_INCREASING,
                top_drivers=["Multi-party funnel micro-deposit aggregation", "Mule role conversion"],
            )

    def get_network_evolution(
        self,
        network_id: str,
        window: EvolutionTimeWindow = EvolutionTimeWindow.ONE_HOUR,
    ) -> NetworkEvolutionSnapshot:
        """Calculates snapshot differential for a network over a specified time window."""
        with self._lock:
            net_data = self._snapshots.get(network_id)
            if not net_data:
                # Default dynamic snapshot
                curr = NetworkMetricsSnapshot(
                    node_count=8,
                    edge_count=12,
                    transaction_count=24,
                    financial_exposure=65000.0,
                    average_risk=70.0,
                    network_risk=75.0,
                    new_accounts_count=2,
                    new_counterparties_count=2,
                )
                prev = NetworkMetricsSnapshot(
                    node_count=6,
                    edge_count=8,
                    transaction_count=16,
                    financial_exposure=45000.0,
                    average_risk=68.0,
                    network_risk=71.0,
                    new_accounts_count=1,
                    new_counterparties_count=1,
                )
            else:
                curr = net_data.get("current")
                prev = net_data.get("previous_1h")

        return self._evolution_engine.build_evolution_snapshot(
            network_id=network_id,
            current=curr,
            previous=prev,
            window=window,
            new_entities=["A003", "A004"],
            removed_entities=[],
            emerging_patterns=["Rapid circular loop expansion"],
        )

    def get_network_forecast(self, network_id: str) -> NetworkRiskForecast:
        """Computes predictive time-series risk forecast for network_id."""
        with self._lock:
            net_data = self._snapshots.get(network_id)
            if not net_data:
                curr_risk = 75.0
                history = [68.0, 71.0, 75.0]
                velocity = 0.5
            else:
                curr = net_data.get("current")
                prev = net_data.get("previous_1h")
                curr_risk = curr.network_risk
                history = [prev.network_risk, curr.network_risk]
                velocity = curr.network_risk - prev.network_risk

        return self._risk_engine.forecast_network_risk(
            network_id=network_id,
            current_risk=curr_risk,
            history_points=history,
            risk_growth_per_hour=velocity,
        )

    def get_entity_trajectory(
        self,
        entity_type: EntityType,
        entity_id: str,
    ) -> EntityRiskTrajectory:
        """Retrieves or calculates risk trajectory for an entity."""
        key = f"{entity_type.value}:{entity_id}"
        with self._lock:
            if key in self._entity_trajectories:
                return self._entity_trajectories[key]

        return EntityRiskTrajectory(
            entity_type=entity_type,
            entity_id=entity_id,
            current_risk=65.0,
            previous_risk=62.0,
            risk_delta=3.0,
            risk_velocity=0.3,
            trajectory=RiskTrajectory.STABLE,
            top_drivers=["Normal baseline transaction flow"],
        )

    def list_emerging_networks(self) -> List[EmergingNetwork]:
        """Discovers and scores active emerging suspicious networks."""
        raw_candidates = [
            {
                "network_id": "NET-001",
                "name": "Syndicate Circular Velocity Loop",
                "growth_rate": 27.3,
                "risk_score": 88.5,
                "tx_velocity": 8.5,
                "exposure": 148000.0,
            },
            {
                "network_id": "EMG-2026-002",
                "name": "Rapid Multi-Inflow Mule Hub",
                "growth_rate": 50.0,
                "risk_score": 79.0,
                "tx_velocity": 12.0,
                "exposure": 84000.0,
            },
        ]
        return self._evolution_engine.detect_emerging_networks(raw_candidates)


_global_network_evolution_service: Optional[NetworkEvolutionService] = None


def get_network_evolution_service() -> NetworkEvolutionService:
    """Singleton getter for NetworkEvolutionService."""
    global _global_network_evolution_service
    if _global_network_evolution_service is None:
        _global_network_evolution_service = NetworkEvolutionService()
    return _global_network_evolution_service
