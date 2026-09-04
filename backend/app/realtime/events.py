"""
FinGraph Real-Time Event Envelope & Strongly Typed Payloads.
Ensures uniform JSON serialization for WebSocket broadcast events across alerts, risk, transactions, cases, and operations.
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
    ALERT_PRIORITIZED = "alert.prioritized"
    ALERT_ASSIGNED = "alert.assigned"
    ALERT_REASSIGNED = "alert.reassigned"
    SLA_WARNING = "sla.warning"
    SLA_BREACHED = "sla.breached"
    TRIAGE_UPDATED = "triage.updated"
    NOTIFICATION_CREATED = "notification.created"
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
    CASE_COMMENT_ADDED = "case.comment_added"
    CASE_COLLABORATOR_ADDED = "case.collaborator_added"
    CASE_COLLABORATOR_REMOVED = "case.collaborator_removed"
    CASE_ACTIVITY_CREATED = "case.activity_created"
    CASE_CORRELATED = "case.correlated"
    CAMPAIGN_DISCOVERED = "campaign.discovered"
    CAMPAIGN_UPDATED = "campaign.updated"
    CAMPAIGN_CONFIRMED = "campaign.confirmed"
    NETWORK_EVOLUTION_CHANGED = "network.evolution_changed"
    NETWORK_RISK_SPIKE = "network.risk_spike"
    NETWORK_EMERGING = "network.emerging"
    ENTITY_RISK_CHANGED = "entity.risk_changed"
    EARLY_WARNING_CREATED = "early_warning.created"
    PATTERN_DISCOVERED = "pattern.discovered"
    THREAT_LEVEL_CHANGED = "threat_level.changed"
    ENTERPRISE_FORECAST_UPDATED = "enterprise.forecast_updated"
    DETECTION_GAP_DETECTED = "detection.gap_detected"
    DETECTION_RECOMMENDATION_CREATED = "detection.recommendation_created"
    DETECTION_RECOMMENDATION_APPROVED = "detection.recommendation_approved"
    DETECTION_RECOMMENDATION_REJECTED = "detection.recommendation_rejected"
    DETECTOR_SHADOW_COMPLETED = "detector.shadow_completed"
    RISK_CALIBRATION_UPDATED = "risk.calibration_updated"
    THREAT_PROPAGATION_DETECTED = "threat.propagation_detected"
    THREAT_PROPAGATION_ESCALATED = "threat.propagation_escalated"
    CORRELATION_CREATED = "correlation.created"
    PRIORITY_UPDATED = "priority.updated"
    INVESTIGATION_BRIEF_READY = "investigation_brief.ready"
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    RECOMMENDATION_CREATED = "recommendation.created"
    WORKFLOW_STATE_CHANGED = "workflow_state.changed"
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


class AlertPrioritizedPayload(BaseModel):
    """Payload emitted when an alert priority score or tier is computed."""
    alert_id: str
    priority_score: float
    priority_level: str
    sla_deadline: datetime
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlertAssignedPayload(BaseModel):
    """Payload emitted when an alert is assigned to an investigator."""
    alert_id: str
    assigned_to: str
    assigned_by: str
    previous_assignee: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlertReassignedPayload(BaseModel):
    """Payload emitted when an alert is reassigned."""
    alert_id: str
    previous_assignee: Optional[str] = None
    new_assignee: str
    reassigned_by: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SLAWarningPayload(BaseModel):
    """Payload emitted when an alert enters the AT_RISK window (<25% SLA remaining)."""
    alert_id: str
    priority_level: str
    time_remaining_minutes: float
    sla_deadline: datetime
    assigned_to: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SLABreachedPayload(BaseModel):
    """Payload emitted when an alert breaches its SLA deadline."""
    alert_id: str
    priority_level: str
    breached_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assigned_to: Optional[str] = None


class TriageUpdatedPayload(BaseModel):
    """Payload emitted when an alert undergoes a valid triage state change."""
    alert_id: str
    previous_status: str
    new_status: str
    actor: str
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationCreatedPayload(BaseModel):
    """Payload emitted when an in-app operational notification is dispatched."""
    notification_id: str
    user_id: Optional[str] = None
    target_role: Optional[str] = None
    type: str
    severity: str
    title: str
    message: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
    change_type: str = "TRANSACTION_ADDED"
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
    update_type: str
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
    action: str
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


class CaseCommentAddedPayload(BaseModel):
    """Payload emitted when a new comment is posted on a case."""
    case_id: str
    comment_id: str
    author_id: str
    author_name: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseCollaboratorAddedPayload(BaseModel):
    """Payload emitted when a collaborator is assigned to a case."""
    case_id: str
    user_id: str
    username: str
    role: str
    added_by: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseCollaboratorRemovedPayload(BaseModel):
    """Payload emitted when a collaborator is removed from a case."""
    case_id: str
    user_id: str
    removed_by: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseActivityCreatedPayload(BaseModel):
    """Payload emitted when an activity feed entry is recorded."""
    event_id: str
    case_id: str
    actor_name: str
    event_type: str
    summary: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseCorrelatedPayload(BaseModel):
    """Payload emitted when cross-case correlation is identified."""
    case_a: str
    case_b: str
    signal_type: str
    signal_strength: float
    confidence: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CampaignDiscoveredPayload(BaseModel):
    """Payload emitted when a new fraud campaign cluster is discovered."""
    campaign_id: str
    name: str
    risk_score: float
    confidence: float
    case_count: int
    exposure: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CampaignUpdatedPayload(BaseModel):
    """Payload emitted when a fraud campaign status or metadata changes."""
    campaign_id: str
    status: str
    risk_score: float
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CampaignConfirmedPayload(BaseModel):
    """Payload emitted when a fraud campaign is confirmed by leadership."""
    campaign_id: str
    name: str
    confirmed_by: str
    confirmed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NetworkEvolutionChangedPayload(BaseModel):
    """Payload emitted when a fraud network evolution snapshot updates."""
    network_id: str
    window: str
    growth_rate: float
    risk_delta: float
    trajectory: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EarlyWarningCreatedPayload(BaseModel):
    """Payload emitted when a proactive early warning trigger fires."""
    warning_id: str
    severity: str
    entity_type: str
    entity_id: str
    risk_score: float
    explanation: str
    recommended_action: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PatternDiscoveredPayload(BaseModel):
    """Payload emitted when a recurring fraud motif is discovered."""
    pattern_id: str
    name: str
    pattern_type: str
    frequency: int
    risk_score: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThreatLevelChangedPayload(BaseModel):
    """Payload emitted when enterprise threat level shifts."""
    threat_level: str
    score: float
    previous_level: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DetectionGapDetectedPayload(BaseModel):
    """Payload emitted when an uncovered detection gap is discovered."""
    gap_id: str
    title: str
    pattern_type: str
    priority: str
    exposure: float
    uncovered_motifs: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DetectionRecommendationPayload(BaseModel):
    """Payload emitted when a detector recommendation is created, approved, or rejected."""
    recommendation_id: str
    status: str
    title: Optional[str] = None
    reviewer: Optional[str] = None
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DetectorShadowCompletedPayload(BaseModel):
    """Payload emitted when a shadow detector simulation completes."""
    simulation_id: str
    detector_id: str
    alerts_would_fire: int
    novel_detections: int
    ground_truth_status: str
    execution_time_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RiskCalibrationUpdatedPayload(BaseModel):
    """Payload emitted when risk calibration metrics are updated."""
    report_id: str
    window_days: int
    overall_confirmation_rate: float
    drift_detected: bool
    adjustments_count: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThreatPropagationDetectedPayload(BaseModel):
    """Payload emitted when multi-hop threat propagation is simulated or escalated."""
    analysis_id: str
    origin_entity_id: str
    propagation_score: float
    total_affected_entities: int
    total_exposure: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def create_realtime_event(event_type: EventType, data: Any) -> RealtimeEvent:
    """Helper factory for creating typed RealtimeEvent instances."""
    return RealtimeEvent(
        event=event_type,
        data=data,
    )
