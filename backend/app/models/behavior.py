"""
FinGraph Behavioral Anomaly & Temporal Intelligence Models (Pydantic V2).
Defines entity baseline profiles, temporal windows, anomaly scores, and similarity vectors.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from detection.src.models import Severity


class TemporalWindow(str, Enum):
    """Configurable temporal analysis windows."""
    WINDOW_5M = "5m"
    WINDOW_1H = "1h"
    WINDOW_24H = "24h"
    WINDOW_7D = "7d"
    WINDOW_30D = "30d"


class AnomalyType(str, Enum):
    """Types of detected behavioral deviations."""
    VOLUME_SPIKE = "VOLUME_SPIKE"
    VELOCITY_BURST = "VELOCITY_BURST"
    COUNTERPARTY_BURST = "COUNTERPARTY_BURST"
    UNUSUAL_OUTGOING_RATIO = "UNUSUAL_OUTGOING_RATIO"
    HIGH_VALUE_DEVIATION = "HIGH_VALUE_DEVIATION"
    NEW_TOPOLOGY_CONNECTION = "NEW_TOPOLOGY_CONNECTION"


class EntityBehaviorBaseline(BaseModel):
    """Statistical historical behavioral baseline for an entity."""
    entity_id: str
    historical_transaction_count: int = 0
    historical_volume: float = 0.0
    avg_transaction_amount: float = 0.0
    std_dev_amount: float = 0.0
    max_transaction_amount: float = 0.0
    avg_velocity_per_hour: float = 0.0
    incoming_volume_ratio: float = 0.5
    outgoing_volume_ratio: float = 0.5
    unique_counterparties_count: int = 0
    common_counterparties: List[str] = Field(default_factory=list)
    baseline_window_days: int = 30
    last_computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BehavioralAnomaly(BaseModel):
    """Detected deviation from baseline behavior."""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: Severity
    anomaly_score: float = Field(..., ge=0.0, le=100.0)
    window: TemporalWindow
    metric_name: str
    observed_value: float
    baseline_value: float
    deviation_ratio: float
    description: str
    evidence_reference: Optional[str] = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EntityBehaviorResponse(BaseModel):
    """Comprehensive behavioral dossier for an entity."""
    entity_id: str
    baseline: EntityBehaviorBaseline
    recent_transaction_count: int
    recent_volume: float
    active_window: TemporalWindow
    anomalies: List[BehavioralAnomaly] = Field(default_factory=list)
    anomaly_score: float = 0.0
    is_anomalous: bool = False
    summary: str


class EntitySimilarityItem(BaseModel):
    """Similarity comparison between the target entity and another suspect entity."""
    target_entity_id: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    shared_counterparties: List[str] = Field(default_factory=list)
    shared_communities: List[int] = Field(default_factory=list)
    shared_detectors: List[str] = Field(default_factory=list)
    volume_similarity: float = 0.0
    explanation: str


class EntitySimilarityResponse(BaseModel):
    """List of most similar entities with explainable factor breakdown."""
    entity_id: str
    similar_entities: List[EntitySimilarityItem]
    total_matches: int
