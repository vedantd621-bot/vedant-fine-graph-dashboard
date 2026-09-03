"""
FinGraph Alert REST Models.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from detection.src.models import AlertStatus, DetectionEvidence, DetectionType, Severity
from analytics.src.models import RiskLevel


class AlertSummary(BaseModel):
    """Compact alert entity for list views and tables."""
    alert_id: str
    detection_type: DetectionType
    severity: Severity
    confidence: float
    primary_account: str
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    created_at: datetime
    status: AlertStatus
    description: str
    total_amount: Optional[float] = None
    currency: str = "USD"


class AlertDetail(BaseModel):
    """Complete alert entity including forensic evidence and related counterparties."""
    alert_id: str
    detection_type: DetectionType
    severity: Severity
    confidence: float
    primary_account: str
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: AlertStatus
    description: str
    evidence: DetectionEvidence
    related_accounts: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    total_amount: Optional[float] = None
    currency: str = "USD"
    reasons: List[str] = Field(default_factory=list)


class AlertStatusUpdateRequest(BaseModel):
    """Request payload for updating an alert's investigation status."""
    status: AlertStatus
    notes: Optional[str] = None
