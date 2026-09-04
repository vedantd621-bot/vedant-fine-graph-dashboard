"""
FinGraph Early Warning Data Models.
Provides structures for proactive alert thresholds, severity levels,
non-destructive investigation recommendations, and audit tracking.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from detection.src.models import Severity


class EarlyWarningSeverity(str, Enum):
    """Severity classification for proactive early warnings."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EarlyWarningStatus(str, Enum):
    """Operational lifecycle state for early warnings."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ESCALATED = "ESCALATED"
    DISMISSED = "DISMISSED"


class WarningActionRecommendation(str, Enum):
    """Recommended non-destructive next steps for investigators."""
    REVIEW_NETWORK = "REVIEW_NETWORK"
    REVIEW_ACCOUNT = "REVIEW_ACCOUNT"
    ESCALATE_CASE = "ESCALATE_CASE"
    MONITOR_ACTIVITY = "MONITOR_ACTIVITY"
    INVESTIGATE_COUNTERPARTIES = "INVESTIGATE_COUNTERPARTIES"
    REVIEW_TRANSACTION_FLOW = "REVIEW_TRANSACTION_FLOW"


class EarlyWarning(BaseModel):
    """Proactive early warning indicating emerging or escalating fraud hazard."""
    warning_id: str = Field(default_factory=lambda: f"WARN-{uuid.uuid4().hex[:8].upper()}")
    severity: EarlyWarningSeverity
    status: EarlyWarningStatus = EarlyWarningStatus.ACTIVE
    entity_type: str
    entity_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    trigger_signals: List[str] = Field(default_factory=list)
    explanation: str
    recommended_action: WarningActionRecommendation
    audit_notes: Optional[str] = None
    acknowledged_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EarlyWarningActionRequest(BaseModel):
    """Payload for acknowledging, escalating, or dismissing a warning."""
    notes: Optional[str] = Field(None, max_length=2000)


class EnterpriseThreatLevel(str, Enum):
    """Enterprise-wide threat level classification."""
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"


class EnterpriseThreatAssessment(BaseModel):
    """Executive composite enterprise threat evaluation."""
    threat_level: EnterpriseThreatLevel
    score: float = Field(..., ge=0.0, le=100.0)
    previous_level: EnterpriseThreatLevel = EnterpriseThreatLevel.NORMAL
    score_delta: float = 0.0
    drivers: List[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EnterpriseRiskForecast(BaseModel):
    """Executive predictive risk forecast over standard horizons."""
    current_threat_score: float
    threat_level: EnterpriseThreatLevel
    forecast_1h: float
    forecast_6h: float
    forecast_24h: float
    forecast_7d: float
    confidence: float
    data_sufficiency: str = "SUFFICIENT_TELEMETRY"
    top_drivers: List[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
