"""
Unit tests for Predictive Risk Forecasting and Entity Trajectories.
"""
import pytest
from backend.app.network_evolution.models import (
    EntityType,
    EvolutionTimeWindow,
    ForecastHorizon,
    ForecastStatus,
    RiskTrajectory,
)
from backend.app.network_evolution.risk import PredictiveRiskEngine
from backend.app.network_evolution.service import NetworkEvolutionService


def test_predictive_risk_forecasting():
    engine = PredictiveRiskEngine()

    # Sufficient history test
    forecast = engine.forecast_network_risk(
        network_id="NET-FORECAST",
        current_risk=75.0,
        history_points=[68.0, 72.0, 75.0],
        risk_growth_per_hour=1.2,
    )

    assert forecast.status == ForecastStatus.SUFFICIENT_DATA
    assert forecast.current_risk == 75.0
    assert ForecastHorizon.NEXT_1H.value in forecast.horizons
    assert ForecastHorizon.NEXT_24H.value in forecast.horizons

    h1 = forecast.horizons[ForecastHorizon.NEXT_1H.value]
    assert h1.forecast_score is not None
    assert h1.forecast_score > 75.0
    assert h1.confidence > 0.85
    assert len(h1.drivers) >= 2


def test_insufficient_history_behavior():
    engine = PredictiveRiskEngine()

    forecast = engine.forecast_network_risk(
        network_id="NET-NEW",
        current_risk=50.0,
        history_points=[50.0],  # Single point
        risk_growth_per_hour=0.0,
    )

    assert forecast.status == ForecastStatus.INSUFFICIENT_HISTORY
    for h in forecast.horizons.values():
        assert h.forecast_score is None
        assert h.status == ForecastStatus.INSUFFICIENT_HISTORY


def test_entity_trajectory_service():
    service = NetworkEvolutionService()

    traj = service.get_entity_trajectory(EntityType.ACCOUNT, "A001")
    assert traj.entity_id == "A001"
    assert traj.current_risk == 92.0
    assert traj.trajectory == RiskTrajectory.INCREASING
    assert len(traj.top_drivers) >= 1
