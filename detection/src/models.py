"""
FinGraph Detection & Alert Data Models (Pydantic V2).
Provides structured, explainable models for graph fraud detections, forensic evidence, and alerts.
"""
from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DetectionType(str, Enum):
    """Supported graph fraud syndicate and anomaly patterns."""
    FUNNEL = "FUNNEL"
    ONE_TO_MANY = "ONE_TO_MANY"
    CHAIN = "CHAIN"
    CIRCULAR_FLOW = "CIRCULAR_FLOW"
    LAYERED_NETWORK = "LAYERED_NETWORK"
    HIGH_DEGREE = "HIGH_DEGREE"
    MONEY_TRAIL = "MONEY_TRAIL"


class Severity(str, Enum):
    """Explainable risk signal severity level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Investigation status lifecycle for generated alerts."""
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class DetectionEvidence(BaseModel):
    """Structured forensic evidence explaining why a pattern was flagged."""
    model_config = ConfigDict(frozen=True, extra="allow")

    reason_summary: str = Field(..., description="Human-readable explanation of the detection")
    metric_name: str = Field(..., description="Primary metric evaluated (e.g. source_count, hop_count)")
    metric_value: Any = Field(..., description="Observed numeric/structural value")
    threshold_value: Any = Field(..., description="Configured rule threshold")
    source_accounts: List[str] = Field(default_factory=list)
    destination_accounts: List[str] = Field(default_factory=list)
    intermediary_accounts: List[str] = Field(default_factory=list)
    path_nodes: List[str] = Field(default_factory=list)
    cycle_length: Optional[int] = None
    hop_count: Optional[int] = None
    inflow_amount: Optional[float] = None
    outflow_amount: Optional[float] = None
    time_window: Optional[str] = None


def generate_fingerprint(
    detection_type: str,
    primary_account: str,
    related_accounts: List[str],
    time_bucket: Optional[str] = None,
) -> str:
    """
    Generates a deterministic SHA256 hex digest for alert deduplication.
    Prevents repeated engine runs from generating duplicate alerts for the same graph topology.
    """
    sorted_related = sorted(list(set(related_accounts)))
    raw_key = f"{detection_type}:{primary_account}:{','.join(sorted_related)}:{time_bucket or 'static'}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]


class DetectionResult(BaseModel):
    """Standardized result produced by Cypher graph pattern detectors."""
    model_config = ConfigDict(frozen=True)

    detection_id: str = Field(..., description="Deterministic unique identifier or fingerprint")
    detection_type: DetectionType = Field(..., description="Type of pattern detected")
    severity: Severity = Field(..., description="Risk signal severity level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Rule-based pattern match confidence (0.0 - 1.0)")
    primary_account: str = Field(..., description="Focal account ID under investigation")
    scenario_id: Optional[str] = Field(default=None, description="Known synthetic scenario tag if available")
    description: str = Field(..., description="Summary description for analysts")
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: DetectionEvidence = Field(..., description="Forensic metrics and topological evidence")
    related_accounts: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    total_amount: Optional[float] = Field(default=None)
    currency: str = Field(default="USD")


class Alert(BaseModel):
    """Actionable alert model dispatched to fraud operations and investigation APIs."""
    model_config = ConfigDict(frozen=True)

    alert_id: str = Field(..., description="Unique alert fingerprint identifier")
    detection_type: DetectionType
    severity: Severity
    confidence: float
    primary_account: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: AlertStatus = Field(default=AlertStatus.OPEN)
    description: str
    evidence: DetectionEvidence
    related_accounts: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    total_amount: Optional[float] = None
    currency: str = "USD"
