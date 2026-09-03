"""
FinGraph Analytics & Explainable Risk Models (Pydantic V2).
Defines schemas for GDS graph features, rule signals, composite risk scores, and assessments.
"""
from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    """Explainable risk band classification for accounts."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GraphFeatures(BaseModel):
    """Topological graph metrics extracted from Neo4j & GDS."""
    model_config = ConfigDict(frozen=True, extra="allow")

    account_id: str = Field(..., description="Unique Account identifier")
    pagerank: float = Field(default=0.0, ge=0.0, description="PageRank network centrality score")
    wcc_id: Optional[int] = Field(default=None, description="Weakly Connected Component partition ID")
    louvain_community_id: Optional[int] = Field(default=None, description="Louvain modular community ID")
    in_degree: int = Field(default=0, ge=0, description="Incoming transaction count")
    out_degree: int = Field(default=0, ge=0, description="Outgoing transaction count")
    total_degree: int = Field(default=0, ge=0, description="Total node degree (in + out)")
    community_size: int = Field(default=1, ge=1, description="Number of member accounts in Louvain community")
    total_volume: float = Field(default=0.0, ge=0.0, description="Total dollar volume transacted through account")


class RuleSignals(BaseModel):
    """Aggregated Phase 6 graph pattern detections for an individual account."""
    model_config = ConfigDict(frozen=True)

    account_id: str = Field(..., description="Target Account identifier")
    funnel_flag: bool = Field(default=False)
    circular_flag: bool = Field(default=False)
    layered_flag: bool = Field(default=False)
    one_to_many_flag: bool = Field(default=False)
    chain_flag: bool = Field(default=False)
    high_degree_flag: bool = Field(default=False)
    active_detections_count: int = Field(default=0, ge=0)
    raw_rule_score: float = Field(default=0.0, ge=0.0, le=100.0)
    detection_types: List[str] = Field(default_factory=list)


class RiskScore(BaseModel):
    """Composite, explainable risk score for an account combining rule & graph signals."""
    model_config = ConfigDict(frozen=True)

    account_id: str = Field(..., description="Evaluated Account identifier")
    score: float = Field(..., ge=0.0, le=100.0, description="Final composite risk score (0 - 100)")
    risk_level: RiskLevel = Field(..., description="Categorical risk band (LOW / MEDIUM / HIGH / CRITICAL)")
    rule_subscore: float = Field(..., ge=0.0, le=100.0, description="Rule-based subscore (0 - 100)")
    graph_subscore: float = Field(..., ge=0.0, le=100.0, description="Graph-analytics subscore (0 - 100)")
    model_version: str = Field(default="rule-gds-v1", description="Risk scoring methodology version")
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    features: GraphFeatures = Field(..., description="Extracted topological graph features")
    rule_signals: RuleSignals = Field(..., description="Active rule detection signals")
    reasons: List[str] = Field(default_factory=list, description="Human-readable explainable rationale bullets")


class RiskAssessment(BaseModel):
    """Persistent audit entity stored in Neo4j graph for historical tracking."""
    model_config = ConfigDict(frozen=True)

    assessment_id: str = Field(..., description="Unique assessment identifier")
    account_id: str
    score: float
    risk_level: RiskLevel
    model_version: str
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reasons: List[str] = Field(default_factory=list)
