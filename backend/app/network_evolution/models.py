"""
FinGraph Network Evolution, Predictive Risk, and Trajectory Data Models.
Provides deterministic data structures for snapshot tracking over bounded windows,
velocity calculations, risk trajectories, emerging network discovery, and risk forecasting.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from analytics.src.models import RiskLevel


class EvolutionTimeWindow(str, Enum):
    """Supported bounded evaluation windows for evolution tracking."""
    FIVE_MINUTES = "5m"
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    TWENTY_FOUR_HOURS = "24h"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"


class RiskTrajectory(str, Enum):
    """Deterministic classification of network and entity risk momentum."""
    STABLE = "STABLE"
    INCREASING = "INCREASING"
    RAPIDLY_INCREASING = "RAPIDLY_INCREASING"
    DECREASING = "DECREASING"
    VOLATILE = "VOLATILE"


class ForecastHorizon(str, Enum):
    """Time horizons for predictive risk forecasting."""
    NEXT_1H = "next_1h"
    NEXT_6H = "next_6h"
    NEXT_24H = "next_24h"
    NEXT_7D = "next_7d"


class ForecastStatus(str, Enum):
    """Data sufficiency indicator for risk forecasts."""
    SUFFICIENT_DATA = "SUFFICIENT_DATA"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"


class NetworkMetricsSnapshot(BaseModel):
    """Point-in-time metrics capture for a fraud network."""
    node_count: int
    edge_count: int
    transaction_count: int
    financial_exposure: float
    average_risk: float
    network_risk: float
    new_accounts_count: int = 0
    new_counterparties_count: int = 0
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NetworkVelocity(BaseModel):
    """Activity and hazard expansion velocity normalized per hour."""
    tx_velocity_per_hour: float = 0.0
    account_velocity_per_hour: float = 0.0
    counterparty_velocity_per_hour: float = 0.0
    exposure_velocity_per_hour: float = 0.0
    risk_growth_per_hour: float = 0.0


class NetworkEvolutionSnapshot(BaseModel):
    """Snapshot differential comparison across a specified bounded time window."""
    network_id: str
    window: EvolutionTimeWindow
    previous_snapshot: Optional[NetworkMetricsSnapshot] = None
    current_snapshot: NetworkMetricsSnapshot
    growth_rate: float
    risk_delta: float
    exposure_delta: float
    velocity: NetworkVelocity
    trajectory: RiskTrajectory
    new_entities: List[str] = Field(default_factory=list)
    removed_entities: List[str] = Field(default_factory=list)
    emerging_patterns: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmergingNetwork(BaseModel):
    """Newly forming suspicious graph component flagged by velocity and anomaly convergence."""
    network_id: str = Field(default_factory=lambda: f"EMG-{uuid.uuid4().hex[:8].upper()}")
    name: str
    emergence_score: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    growth_metrics: Dict[str, float] = Field(default_factory=dict)
    supporting_signals: List[str] = Field(default_factory=list)
    explanation: str
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HorizonForecast(BaseModel):
    """Single horizon risk projection."""
    horizon: ForecastHorizon
    forecast_score: Optional[float] = None
    confidence: float = 0.0
    trend: str = "STABLE"
    drivers: List[str] = Field(default_factory=list)
    status: ForecastStatus = ForecastStatus.SUFFICIENT_DATA


class NetworkRiskForecast(BaseModel):
    """Comprehensive predictive risk forecast across all horizons."""
    network_id: str
    current_risk: float
    horizons: Dict[str, HorizonForecast] = Field(default_factory=dict)
    overall_trend: RiskTrajectory
    status: ForecastStatus
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EntityType(str, Enum):
    """Entity types tracked for risk trajectory and momentum."""
    ACCOUNT = "account"
    DEVICE = "device"
    IP = "ip"
    COUNTERPARTY = "counterparty"
    NETWORK = "network"


class EntityRiskTrajectory(BaseModel):
    """Risk momentum and driver evaluation for a specific entity."""
    entity_type: EntityType
    entity_id: str
    current_risk: float
    previous_risk: float
    risk_delta: float
    risk_velocity: float
    trajectory: RiskTrajectory
    top_drivers: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
