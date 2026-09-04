"""
FinGraph Predictive Risk & Time-Series Forecasting.
Provides deterministic risk forecasts across 1h, 6h, 24h, and 7d horizons
with historical data sufficiency checks and trajectory damping.
"""
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional

from backend.app.network_evolution.models import (
    ForecastHorizon,
    ForecastStatus,
    HorizonForecast,
    NetworkRiskForecast,
    RiskTrajectory,
)

logger = logging.getLogger("FinGraph.PredictiveRisk")

HORIZON_HOURS = {
    ForecastHorizon.NEXT_1H: 1.0,
    ForecastHorizon.NEXT_6H: 6.0,
    ForecastHorizon.NEXT_24H: 24.0,
    ForecastHorizon.NEXT_7D: 168.0,
}


class PredictiveRiskEngine:
    """Calculates deterministic, explainable risk projections."""

    def __init__(self):
        pass

    def forecast_network_risk(
        self,
        network_id: str,
        current_risk: float,
        history_points: List[float],
        risk_growth_per_hour: float = 0.0,
    ) -> NetworkRiskForecast:
        """
        Forecasts risk score for 1h, 6h, 24h, and 7d horizons:
        Forecast(h) = CurrentRisk + Velocity * h * DampingFactor(h).
        If history_points < 2, explicitly returns INSUFFICIENT_HISTORY.
        """
        if len(history_points) < 2:
            return NetworkRiskForecast(
                network_id=network_id,
                current_risk=current_risk,
                horizons={
                    h.value: HorizonForecast(
                        horizon=h,
                        forecast_score=None,
                        confidence=0.0,
                        trend="UNKNOWN",
                        drivers=["Insufficient historical telemetry to project risk trend"],
                        status=ForecastStatus.INSUFFICIENT_HISTORY,
                    )
                    for h in ForecastHorizon
                },
                overall_trend=RiskTrajectory.STABLE,
                status=ForecastStatus.INSUFFICIENT_HISTORY,
            )

        horizons_dict: Dict[str, HorizonForecast] = {}
        for h in ForecastHorizon:
            hours = HORIZON_HOURS[h]
            damping = 1.0 / (1.0 + 0.04 * hours)  # Damping prevents exponential runaway
            raw_proj = current_risk + (risk_growth_per_hour * hours * damping)
            score = round(min(100.0, max(0.0, raw_proj)), 1)

            trend = (
                "RAPIDLY_INCREASING" if score - current_risk >= 15.0
                else "INCREASING" if score - current_risk >= 5.0
                else "DECREASING" if current_risk - score >= 5.0
                else "STABLE"
            )

            confidence = round(max(0.60, min(0.95, 0.95 - (hours * 0.0015))), 2)

            drivers = [
                f"Base current risk index: {current_risk:.1f}",
                f"Observed risk velocity: {risk_growth_per_hour:+.2f} pts/hr",
                f"Horizon damping factor: {damping:.2f}",
            ]

            horizons_dict[h.value] = HorizonForecast(
                horizon=h,
                forecast_score=score,
                confidence=confidence,
                trend=trend,
                drivers=drivers,
                status=ForecastStatus.SUFFICIENT_DATA,
            )

        overall_trend = (
            RiskTrajectory.RAPIDLY_INCREASING if risk_growth_per_hour >= 1.5
            else RiskTrajectory.INCREASING if risk_growth_per_hour >= 0.3
            else RiskTrajectory.DECREASING if risk_growth_per_hour <= -0.3
            else RiskTrajectory.STABLE
        )

        return NetworkRiskForecast(
            network_id=network_id,
            current_risk=current_risk,
            horizons=horizons_dict,
            overall_trend=overall_trend,
            status=ForecastStatus.SUFFICIENT_DATA,
        )
