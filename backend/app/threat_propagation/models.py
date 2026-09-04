"""
FinGraph Threat Propagation Data Models.
Provides deterministic data structures for multi-hop graph contagion modeling,
timeline steps, 6-factor propagation scoring, and interactive topologies.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class PropagationMechanism(str, Enum):
    """Graph mechanism facilitating threat transmission."""
    DIRECT_TRANSFER = "DIRECT_TRANSFER"
    SHARED_CREDENTIAL = "SHARED_CREDENTIAL"
    COUNTERPARTY_CLUSTER = "COUNTERPARTY_CLUSTER"
    RAPID_FANOUT = "RAPID_FANOUT"
    PROXY_HOP = "PROXY_HOP"


class PropagationStep(BaseModel):
    """Discrete progression step in the threat expansion timeline."""
    step_index: int
    step_time_offset_sec: int
    mechanism: PropagationMechanism
    reached_entities: List[str]
    new_exposure_amount: float
    step_risk_delta: float
    description: str


class PropagatedEntity(BaseModel):
    """Entity node reached during contagion simulation."""
    entity_id: str
    entity_type: str = "ACCOUNT"
    distance_from_origin: int
    risk_score: float
    exposure_amount: float
    infection_probability: float = Field(ge=0.0, le=1.0)
    propagation_path: List[str]


class PropagationTopologyNode(BaseModel):
    """Graph node for visualization."""
    id: str
    label: str
    risk: float
    hop: int
    exposure: float
    type: str = "ACCOUNT"


class PropagationTopologyEdge(BaseModel):
    """Graph edge for visualization."""
    source: str
    target: str
    amount: float
    mechanism: str
    step: int


class PropagationTopology(BaseModel):
    """D3-compatible graph representation of threat propagation."""
    nodes: List[PropagationTopologyNode]
    edges: List[PropagationTopologyEdge]


class ThreatPropagationAnalysis(BaseModel):
    """Comprehensive multi-hop threat propagation evaluation."""
    analysis_id: str = Field(default_factory=lambda: f"prop_{uuid.uuid4().hex[:10]}")
    origin_entity_id: str
    max_hops: int = Field(ge=1, le=5)
    time_window_hours: int = Field(ge=1, le=168)
    propagation_score: float = Field(ge=0.0, le=100.0)
    risk_velocity: float
    total_affected_entities: int
    total_financial_exposure: float
    steps: List[PropagationStep]
    affected_entities_details: List[PropagatedEntity]
    topology: PropagationTopology
    containment_recommendations: List[str]
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
