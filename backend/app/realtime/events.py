"""
FinGraph Real-Time Event Envelope & Strongly Typed Payloads.
Ensures uniform JSON serialization for WebSocket broadcast events across alerts, risk, transactions, and cases.
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
    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"
    INVESTIGATION_UPDATED = "investigation.updated"
    ACCOUNT_FROZEN = "account.frozen"
    NETWORK_CREATED = "network.created"
    NETWORK_UPDATED = "network.updated"
    NETWORK_RISK_UPDATED = "network.risk_updated"
    ANOMALY_DETECTED = "anomaly.detected"
    ENTITY_BEHAVIOR_CHANGED = "entity.behavior_changed"
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


class CaseCreatedPayload(BaseModel):
    """Payload emitted when a new investigation case is opened."""
    case_id: str
    title: str
    priority: str
    status: str
    assigned_investigator: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseUpdatedPayload(BaseModel):
    """Payload emitted when a case's status, assignment, or notes are modified."""
    case_id: str
    status: str
    priority: str
    assigned_investigator: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: str = "UPDATE"


class InvestigationUpdatedPayload(BaseModel):
    """Payload emitted when evidence or notes are attached to an active investigation."""
    case_id: str
    update_type: str  # "NOTE_ADDED", "EVIDENCE_ATTACHED", "ALERT_LINKED", "ACCOUNT_LINKED"
    author: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detail: Optional[str] = None


class AccountFrozenPayload(BaseModel):
    """Payload emitted when an account's freeze state is toggled."""
    account_id: str
    is_frozen: bool
    actor: str
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NetworkCreatedPayload(BaseModel):
    """Payload emitted when a new fraud network is discovered."""
    network_id: str
    name: str
    network_type: str
    risk_score: float
    risk_level: str
    member_count: int
    total_volume: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NetworkUpdatedPayload(BaseModel):
    """Payload emitted when a fraud network is mutated or linked to a case."""
    network_id: str
    action: str  # "MEMBER_ADDED", "CASE_LINKED", "ALERT_LINKED", "STATUS_UPDATED"
    risk_score: float
    member_count: int
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NetworkRiskUpdatedPayload(BaseModel):
    """Payload emitted when a fraud network's composite risk score is recalculated."""
    network_id: str
    risk_score: float
    risk_level: str
    contributing_factors_count: int
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnomalyDetectedPayload(BaseModel):
    """Payload emitted when a behavioral anomaly deviation is flagged."""
    anomaly_id: str
    entity_id: str
    anomaly_type: str
    severity: str
    anomaly_score: float
    window: str
    metric_name: str
    observed_value: float
    baseline_value: float
    deviation_ratio: float
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EntityBehaviorChangedPayload(BaseModel):
    """Payload emitted when an entity's baseline or active profile updates."""
    entity_id: str
    anomaly_score: float
    is_anomalous: bool
    active_anomalies_count: int
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
