"""
FinGraph Pattern Discovery & Structural Similarity Models.
Provides data structures for recurring fraud motifs, topological frequency,
confidence metrics, and explainable pattern similarity comparisons.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class PatternType(str, Enum):
    """Classifications of discovered fraud motifs."""
    CIRCULAR_LOOP = "CIRCULAR_LOOP"
    RAPID_DISPERSION = "RAPID_DISPERSION"
    MULTI_INFLOW_FUNNEL = "MULTI_INFLOW_FUNNEL"
    BURST_ACTIVITY = "BURST_ACTIVITY"
    LAYERED_CHAIN = "LAYERED_CHAIN"


class DiscoveredPattern(BaseModel):
    """Recurring fraud motif extracted across graph topology, alerts, and campaigns."""
    pattern_id: str = Field(default_factory=lambda: f"PAT-{uuid.uuid4().hex[:8].upper()}")
    name: str
    pattern_type: PatternType
    frequency: int
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=100.0)
    affected_entities: List[str] = Field(default_factory=list)
    financial_exposure: float = 0.0
    explanation: str
    supporting_signals: List[str] = Field(default_factory=list)
    related_cases: List[str] = Field(default_factory=list)
    related_campaigns: List[str] = Field(default_factory=list)
    related_networks: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PatternSimilarityResponse(BaseModel):
    """Explainable structural and entity similarity comparison between two patterns."""
    pattern_a: str
    pattern_b: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    shared_signals: List[str] = Field(default_factory=list)
    shared_entities: List[str] = Field(default_factory=list)
    explanation: str
