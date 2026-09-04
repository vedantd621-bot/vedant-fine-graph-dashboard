"""
FinGraph Shadow Detection Data Models.
Provides deterministic data structures for sandbox testing of candidate detectors against historical telemetry.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class GroundTruthStatus(str, Enum):
    """Indicates if validated ground truth was available to calculate precision/recall."""
    SUFFICIENT_GROUND_TRUTH = "SUFFICIENT_GROUND_TRUTH"
    INSUFFICIENT_GROUND_TRUTH = "INSUFFICIENT_GROUND_TRUTH"


class ShadowSimulationRequest(BaseModel):
    """Request payload to initiate a shadow detection simulation run."""
    detector_id: str
    recommendation_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    time_window_hours: int = Field(default=24, ge=1, le=720)
    sample_size_limit: int = Field(default=10000, ge=100, le=100000)


class ShadowSimulationResult(BaseModel):
    """Deterministic evaluation output from a shadow simulation run."""
    simulation_id: str = Field(default_factory=lambda: f"sim_{uuid.uuid4().hex[:10]}")
    detector_id: str
    recommendation_id: Optional[str] = None
    time_window_hours: int
    transactions_evaluated_count: int
    alerts_would_fire_count: int
    overlap_with_prod_alerts_count: int
    novel_detections_count: int
    estimated_precision: Optional[float] = None
    estimated_recall: Optional[float] = None
    estimated_fpr: float = Field(ge=0.0, le=1.0)
    ground_truth_status: GroundTruthStatus
    coverage_percentage: float = Field(ge=0.0, le=100.0)
    findings_summary: str
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_time_ms: float
    evaluated_parameters: Dict[str, Any] = Field(default_factory=dict)
