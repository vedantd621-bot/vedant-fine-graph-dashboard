"""
FinGraph Real-Time Event Envelope & Strongly Typed Payloads.
Ensures uniform JSON serialization for WebSocket broadcast events.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
import uuid
from pydantic import BaseModel, Field

from detection.src.models import AlertStatus, DetectionType, Severity
from analytics.src.models import RiskLevel


class EventType(str, Enum):
    """Supported real-time WebSocket event classifications."""
    ALERT_CREATED = "alert.created"
    ALERT_UPDATED = "alert.updated"
    RISK_UPDATED = "risk.updated"
    TRANSACTION_CREATED = "transaction.created"
    GRAPH_UPDATED = "graph.updated"
    SYSTEM_PING = "system.ping"
    SYSTEM_PONG = "system.pong"
    ERROR = "error"


T = TypeVar("T")


class RealtimeEvent(BaseModel, Generic[T]):
    """Standardized event envelope with versioning, UUID, and UTC timestamp."""
    event: EventType
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = Field(default=1)
    data: T

    def to_json_dict(self) -> Dict[str, Any]:
        """Serializes event to clean JSON-compatible dictionary."""
        return self.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Specific Event Payload Schemas
# ---------------------------------------------------------------------------

class AlertCreatedPayload(BaseModel):
    """Payload emitted when a new topological fraud alert is detected."""
    alert_id: str
    detection_type: DetectionType
    severity: Severity
    confidence: float
    primary_account: str
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    status: AlertStatus = AlertStatus.OPEN
    description: str
    total_amount: Optional[float] = None
    currency: str = "USD"
    related_accounts: List[str] = Field(default_factory=list)


class AlertUpdatedPayload(BaseModel):
    """Payload emitted when an alert's investigation lifecycle status changes."""
    alert_id: str
    previous_status: Optional[AlertStatus] = None
    status: AlertStatus
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None


class RiskUpdatedPayload(BaseModel):
    """Payload emitted when an account's composite risk score or level is updated."""
    account_id: str
    previous_score: Optional[float] = None
    score: float
    previous_level: Optional[RiskLevel] = None
    risk_level: RiskLevel
    model_version: str = "rule-gds-v1"
    reasons: List[str] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TransactionCreatedPayload(BaseModel):
    """Payload emitted when a settled transaction event flows through the pipeline."""
    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str = "USD"
    timestamp: datetime
    transaction_type: str = "transfer"
    scenario_id: Optional[str] = None
    channel: Optional[str] = None


class GraphUpdatedPayload(BaseModel):
    """Payload emitted when the graph topology for an account changes."""
    account_id: str
    change_type: str = "TRANSACTION_ADDED"  # "TRANSACTION_ADDED", "ACCOUNT_FROZEN", "COMMUNITY_CHANGED"
    related_account_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorPayload(BaseModel):
    """Structured WebSocket error payload."""
    code: str
    message: str
    details: Optional[Any] = None


def create_realtime_event(event_type: EventType, data: Any) -> RealtimeEvent:
    """Helper factory for creating typed RealtimeEvent instances."""
    return RealtimeEvent(
        event=event_type,
        data=data,
    )
