"""
Unit tests for Network Evolution and Activity Velocity calculations.
"""
import pytest
from backend.app.network_evolution.evolution import NetworkEvolutionEngine
from backend.app.network_evolution.models import (
    EvolutionTimeWindow,
    NetworkMetricsSnapshot,
    RiskTrajectory,
)


def test_velocity_and_snapshot_diffing():
    engine = NetworkEvolutionEngine()

    prev = NetworkMetricsSnapshot(
        node_count=10,
        edge_count=15,
        transaction_count=30,
        financial_exposure=50000.0,
        average_risk=70.0,
        network_risk=72.0,
        new_accounts_count=2,
        new_counterparties_count=3,
    )

    curr = NetworkMetricsSnapshot(
        node_count=15,
        edge_count=25,
        transaction_count=60,
        financial_exposure=120000.0,
        average_risk=80.0,
        network_risk=88.0,
        new_accounts_count=5,
        new_counterparties_count=6,
    )

    snapshot = engine.build_evolution_snapshot(
        network_id="NET-TEST",
        current=curr,
        previous=prev,
        window=EvolutionTimeWindow.ONE_HOUR,
    )

    assert snapshot.network_id == "NET-TEST"
    assert snapshot.growth_rate == 50.0  # (15-10)/10 * 100
    assert snapshot.risk_delta == 16.0   # 88 - 72
    assert snapshot.exposure_delta == 70000.0
    assert snapshot.trajectory == RiskTrajectory.INCREASING

    # Velocity checks
    assert snapshot.velocity.tx_velocity_per_hour == 30.0  # (60-30)/1h
    assert snapshot.velocity.account_velocity_per_hour == 5.0
    assert snapshot.velocity.exposure_velocity_per_hour == 70000.0


def test_trajectory_classification_thresholds():
    engine = NetworkEvolutionEngine()

    assert engine.classify_trajectory(60.0, 75.0, -15.0) == RiskTrajectory.DECREASING
    assert engine.classify_trajectory(75.0, 72.0, 3.0) == RiskTrajectory.STABLE
    assert engine.classify_trajectory(85.0, 70.0, 15.0) == RiskTrajectory.INCREASING
    assert engine.classify_trajectory(95.0, 65.0, 30.0) == RiskTrajectory.RAPIDLY_INCREASING


def test_emerging_networks_detection():
    engine = NetworkEvolutionEngine()

    networks = [
        {"network_id": "N1", "name": "Surge Cluster", "growth_rate": 45.0, "risk_score": 85.0, "tx_velocity": 15.0, "exposure": 80000.0},
        {"network_id": "N2", "name": "Dormant Cluster", "growth_rate": 0.0, "risk_score": 20.0, "tx_velocity": 0.1, "exposure": 500.0},
    ]

    emerging = engine.detect_emerging_networks(networks)
    assert len(emerging) == 1
    assert emerging[0].network_id == "N1"
    assert emerging[0].emergence_score >= 60.0
    assert len(emerging[0].supporting_signals) >= 2
