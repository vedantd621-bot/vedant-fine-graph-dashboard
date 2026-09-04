"""
FinGraph Intelligence Orchestration Data Models.
Provides deterministic data structures for cross-alert correlation, priority scoring,
ranked evidence dossiers, automated briefs, workflow templates, task management,
checklists, unified forensic timelines, related cases, and investigation recommendations.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class WorkflowState(str, Enum):
    """Explicit lifecycle states for investigation cases."""
    CREATED = "CREATED"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    EVIDENCE_REVIEW = "EVIDENCE_REVIEW"
    DECISION_PENDING = "DECISION_PENDING"
    DECIDED = "DECIDED"
    CLOSED = "CLOSED"


class PriorityBand(str, Enum):
    """Investigation priority classification bands."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EvidenceStrength(str, Enum):
    """Deterministic tiering of forensic evidence credibility."""
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvidenceCategory(str, Enum):
    """Classification of forensic evidence sources."""
    TRANSACTION = "TRANSACTION"
    GRAPH = "GRAPH"
    BEHAVIOR = "BEHAVIOR"
    NETWORK = "NETWORK"
    CAMPAIGN = "CAMPAIGN"
    CASE_HISTORY = "CASE_HISTORY"
    DECISION_HISTORY = "DECISION_HISTORY"
    THREAT_PROPAGATION = "THREAT_PROPAGATION"


class CorrelationReason(str, Enum):
    """Explainable signals linking distinct alerts."""
    SHARED_ACCOUNT = "SHARED_ACCOUNT"
    SHARED_DEVICE = "SHARED_DEVICE"
    SHARED_COUNTERPARTY = "SHARED_COUNTERPARTY"
    SHARED_IP = "SHARED_IP"
    SHARED_MERCHANT = "SHARED_MERCHANT"
    TRANSACTION_PATTERN = "TRANSACTION_PATTERN"
    SHARED_NETWORK = "SHARED_NETWORK"
    SHARED_CAMPAIGN = "SHARED_CAMPAIGN"
    TEMPORAL_PROXIMITY = "TEMPORAL_PROXIMITY"
    BEHAVIOR_SIMILARITY = "BEHAVIOR_SIMILARITY"
    RISK_SIMILARITY = "RISK_SIMILARITY"


class TaskStatus(str, Enum):
    """Investigation task execution status."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkflowType(str, Enum):
    """Standardized investigation workflow templates."""
    ACCOUNT_TAKEOVER = "ACCOUNT_TAKEOVER"
    MONEY_MULE = "MONEY_MULE"
    PAYMENT_FRAUD = "PAYMENT_FRAUD"
    CARD_FRAUD = "CARD_FRAUD"
    NETWORK_FRAUD = "NETWORK_FRAUD"
    SUSPICIOUS_VELOCITY = "SUSPICIOUS_VELOCITY"
    COORDINATED_ACTIVITY = "COORDINATED_ACTIVITY"


class PriorityFactor(BaseModel):
    """Individual contributing factor to investigation priority score."""
    name: str
    weight: float
    raw_value: float
    weighted_score: float
    description: str


class InvestigationPriorityScore(BaseModel):
    """Deterministic investigation priority assessment."""
    priority_score: float = Field(ge=0.0, le=100.0)
    priority_band: PriorityBand
    factors: List[PriorityFactor]
    explanation: str
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RankedEvidenceItem(BaseModel):
    """Forensic evidence item with strength classification and provenance."""
    evidence_id: str = Field(default_factory=lambda: f"evi_{uuid.uuid4().hex[:10]}")
    category: EvidenceCategory
    title: str
    description: str
    strength: EvidenceStrength
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    explanation: str
    weight: float = Field(default=1.0, ge=0.0)
    raw_data: Optional[Dict[str, Any]] = None


class CorrelationGroup(BaseModel):
    """Multi-signal correlation linking related alerts."""
    group_id: str = Field(default_factory=lambda: f"grp_{uuid.uuid4().hex[:10]}")
    primary_alert_id: str
    correlated_alert_ids: List[str]
    correlation_score: float = Field(ge=0.0, le=1.0)
    reasons: List[CorrelationReason]
    shared_signals: Dict[str, Any] = Field(default_factory=dict)
    explanation: str
    correlated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UnifiedTimelineEvent(BaseModel):
    """Chronological event in the unified forensic timeline."""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:10]}")
    timestamp: datetime
    event_type: str
    title: str
    description: str
    source: str
    actor: Optional[str] = None
    entity_refs: List[str] = Field(default_factory=list)
    severity: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InvestigationTask(BaseModel):
    """Task assigned to investigators within an active case."""
    task_id: str = Field(default_factory=lambda: f"tsk_{uuid.uuid4().hex[:10]}")
    case_id: str
    title: str
    description: str
    priority: PriorityBand = PriorityBand.MEDIUM
    assignee: str
    status: TaskStatus = TaskStatus.OPEN
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    evidence_refs: List[str] = Field(default_factory=list)
    audit_refs: List[str] = Field(default_factory=list)


class CaseChecklistItem(BaseModel):
    """Checklist action item for case progression."""
    item_id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:8]}")
    case_id: str
    title: str
    is_completed: bool = False
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    order: int = 0


class RelatedCase(BaseModel):
    """Linked historical or concurrent investigation case."""
    case_id: str
    relationship_score: float = Field(ge=0.0, le=1.0)
    relationship_reasons: List[str]
    shared_entities: List[str]
    status: str
    created_at: datetime


class InvestigationRecommendation(BaseModel):
    """Advisory next-step recommended for the investigator."""
    recommendation_id: str = Field(default_factory=lambda: f"irec_{uuid.uuid4().hex[:8]}")
    case_id: str
    title: str
    reason: str
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    priority: PriorityBand = PriorityBand.MEDIUM
    action_type: str
    is_actioned: bool = False


class InvestigationWorkflowTemplate(BaseModel):
    """Standardized investigation workflow procedure template."""
    template_id: str
    name: str
    workflow_type: WorkflowType
    trigger_conditions: List[str]
    required_checks: List[str]
    recommended_evidence: List[str]
    recommended_actions: List[str]
    completion_conditions: List[str]


class InvestigationBrief(BaseModel):
    """Comprehensive synthesized dossier for a fraud case or alert."""
    brief_id: str = Field(default_factory=lambda: f"brf_{uuid.uuid4().hex[:10]}")
    case_or_alert_id: str
    title: str
    executive_summary: str
    risk_summary: str
    financial_exposure: float
    network_summary: str
    behavior_summary: str
    priority_assessment: InvestigationPriorityScore
    related_alerts: List[str]
    related_cases: List[RelatedCase]
    campaign_associations: List[str]
    ranked_evidence: List[RankedEvidenceItem]
    unified_timeline: List[UnifiedTimelineEvent]
    threat_propagation_summary: str
    recommended_investigation_steps: List[InvestigationRecommendation]
    open_questions: List[str]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowStateTransitionRequest(BaseModel):
    """Request payload to transition case workflow state."""
    to_state: WorkflowState
    notes: Optional[str] = None


class TaskCreateRequest(BaseModel):
    """Request payload to create an investigation task."""
    case_id: str
    title: str
    description: str
    priority: PriorityBand = PriorityBand.MEDIUM
    assignee: str
    due_at: Optional[datetime] = None
    evidence_refs: List[str] = Field(default_factory=list)


class TaskUpdateRequest(BaseModel):
    """Request payload to update an investigation task."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[PriorityBand] = None
    assignee: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_at: Optional[datetime] = None


class ChecklistItemCreateRequest(BaseModel):
    """Request payload to add a checklist item."""
    title: str
    order: Optional[int] = 0


class ChecklistItemUpdateRequest(BaseModel):
    """Request payload to check/uncheck a checklist item."""
    is_completed: bool
