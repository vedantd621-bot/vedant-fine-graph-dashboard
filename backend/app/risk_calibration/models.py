"""
FinGraph Risk Calibration Data Models.
Provides deterministic data structures for risk score bucket outcomes, confirmation rates, and threshold adjustments.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class ScoreBucket(BaseModel):
    """Empirical outcome metrics for a defined risk score range."""
    bucket_id: str
    range_min: float
    range_max: float
    total_scored_entities: int
    investigated_entities: int
    confirmed_fraud_count: int
    false_positive_count: int
    confirmation_rate: float = Field(ge=0.0, le=1.0)
    false_positive_rate: float = Field(ge=0.0, le=1.0)


class ThresholdAdjustmentSuggestion(BaseModel):
    """Deterministic proposal to adjust risk score boundaries or detector firing cutoffs."""
    suggestion_id: str = Field(default_factory=lambda: f"adj_{uuid.uuid4().hex[:8]}")
    target_metric_or_detector: str
    current_threshold: float
    suggested_threshold: float
    expected_fpr_reduction_pct: float
    expected_true_positive_retention_pct: float
    rationale: str


class RiskCalibrationReport(BaseModel):
    """Comprehensive calibration analysis of risk scores vs empirical investigation outcomes."""
    report_id: str = Field(default_factory=lambda: f"cal_{uuid.uuid4().hex[:10]}")
    evaluation_window_days: int = Field(default=30)
    buckets: List[ScoreBucket]
    overall_confirmation_rate: float = Field(ge=0.0, le=1.0)
    drift_detected: bool = Field(default=False)
    drift_magnitude: float = Field(default=0.0)
    suggested_adjustments: List[ThresholdAdjustmentSuggestion] = Field(default_factory=list)
    calibration_notes: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
