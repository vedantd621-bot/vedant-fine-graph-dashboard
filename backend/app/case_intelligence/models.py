"""
FinGraph Case Intelligence, Fraud Campaign, and Collaboration Data Models.
Provides deterministic models for cross-case correlation, relationship graphs,
fraud campaigns, collaborator management, case comments, immutable activity feeds,
evidence provenance tracing, and enterprise fraud posture evaluation.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from detection.src.models import Severity
from analytics.src.models import RiskLevel
from backend.app.models.cases import CasePriority, CaseStatus


class CaseCorrelationSignal(str, Enum):
    """Classification of signals connecting separate investigation cases."""
    SHARED_ACCOUNT = "SHARED_ACCOUNT"
    SHARED_COUNTERPARTY = "SHARED_COUNTERPARTY"
    SHARED_NETWORK = "SHARED_NETWORK"
    SHARED_DETECTOR = "SHARED_DETECTOR"
    BEHAVIORAL_SIMILARITY = "BEHAVIORAL_SIMILARITY"
    TEMPORAL_CLUSTERING = "TEMPORAL_CLUSTERING"
    FINANCIAL_FLOW = "FINANCIAL_FLOW"


class CaseCorrelation(BaseModel):
    """Deterministic correlation link between two investigation cases."""
    correlation_id: str = Field(default_factory=lambda: f"CORR-{uuid.uuid4().hex[:10].upper()}")
    case_a: str
    case_b: str
    signal_type: CaseCorrelationSignal
    signal_strength: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    common_entities: List[str] = Field(default_factory=list)
    common_detectors: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseRelationshipNodeType(str, Enum):
    """Types of entities in the bounded Case Relationship Graph."""
    CASE = "CASE"
    ALERT = "ALERT"
    ACCOUNT = "ACCOUNT"
    TRANSACTION = "TRANSACTION"
    NETWORK = "NETWORK"
    EVIDENCE = "EVIDENCE"
    DECISION = "DECISION"


class CaseRelationshipEdgeType(str, Enum):
    """Relationships linking graph nodes in the Case Relationship Graph."""
    LINKS_TO = "LINKS_TO"
    CORRELATED_WITH = "CORRELATED_WITH"
    MEMBER_OF = "MEMBER_OF"
    TRIGGERS = "TRIGGERS"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"
    RESOLVES = "RESOLVES"


class CaseRelationshipNode(BaseModel):
    """Node in the Case Relationship Graph."""
    id: str
    label: str
    type: CaseRelationshipNodeType
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseRelationshipEdge(BaseModel):
    """Directed edge in the Case Relationship Graph."""
    id: str = Field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:8]}")
    source: str
    target: str
    type: CaseRelationshipEdgeType
    strength: float = 1.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseRelationshipGraph(BaseModel):
    """Bounded graph representation of case connections and forensic context."""
    focal_case_id: str
    nodes: List[CaseRelationshipNode]
    edges: List[CaseRelationshipEdge]
    total_nodes: int
    total_edges: int
    truncated: bool = False


class CampaignStatus(str, Enum):
    """Operational lifecycle statuses for multi-case fraud campaigns."""
    DISCOVERED = "DISCOVERED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"
    CLOSED = "CLOSED"


class CampaignRiskFactor(BaseModel):
    """Individual factor contributing to a fraud campaign's risk score."""
    factor_name: str
    weight: float
    raw_value: float
    contribution: float
    evidence: str


class CampaignRiskExplanation(BaseModel):
    """Explainable breakdown of a fraud campaign's 6-factor composite risk."""
    campaign_id: str
    risk_score: float
    confidence: float
    factors: List[CampaignRiskFactor]
    summary: str


class Campaign(BaseModel):
    """Coordinated multi-case fraud syndicate or campaign."""
    campaign_id: str = Field(default_factory=lambda: f"CMP-{uuid.uuid4().hex[:8].upper()}")
    name: str
    description: str
    status: CampaignStatus = CampaignStatus.DISCOVERED
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    case_ids: List[str] = Field(default_factory=list)
    account_ids: List[str] = Field(default_factory=list)
    network_ids: List[str] = Field(default_factory=list)
    alert_ids: List[str] = Field(default_factory=list)
    financial_exposure: float = 0.0
    confirmed_fraud_value: float = 0.0
    potential_exposure: float = 0.0
    primary_signals: List[CaseCorrelationSignal] = Field(default_factory=list)
    factor_contributions: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CollaboratorRole(str, Enum):
    """Investigator role on a case."""
    OWNER = "OWNER"
    COLLABORATOR = "COLLABORATOR"
    WATCHER = "WATCHER"


class CaseCollaborator(BaseModel):
    """Collaborator assigned to a case with explicit access permissions."""
    collaborator_id: str = Field(default_factory=lambda: f"COL-{uuid.uuid4().hex[:8].upper()}")
    case_id: str
    user_id: str
    username: str
    role: CollaboratorRole
    added_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseComment(BaseModel):
    """Auditable investigation comment on a case."""
    comment_id: str = Field(default_factory=lambda: f"CMT-{uuid.uuid4().hex[:8].upper()}")
    case_id: str
    author_id: str
    author_name: str
    content: str
    is_edited: bool = False
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseActivityEventType(str, Enum):
    """Granular audit classifications for case activity log."""
    CASE_CREATED = "CASE_CREATED"
    CASE_ASSIGNED = "CASE_ASSIGNED"
    CASE_REASSIGNED = "CASE_REASSIGNED"
    CASE_STATUS_CHANGED = "CASE_STATUS_CHANGED"
    EVIDENCE_ADDED = "EVIDENCE_ADDED"
    EVIDENCE_UPDATED = "EVIDENCE_UPDATED"
    COMMENT_ADDED = "COMMENT_ADDED"
    COMMENT_UPDATED = "COMMENT_UPDATED"
    COMMENT_DELETED = "COMMENT_DELETED"
    COLLABORATOR_ADDED = "COLLABORATOR_ADDED"
    COLLABORATOR_REMOVED = "COLLABORATOR_REMOVED"
    CAMPAIGN_LINKED = "CAMPAIGN_LINKED"
    CAMPAIGN_STATUS_CHANGED = "CAMPAIGN_STATUS_CHANGED"
    CASE_CORRELATED = "CASE_CORRELATED"


class CaseActivityEvent(BaseModel):
    """Immutable chronological event in the case investigation feed."""
    event_id: str = Field(default_factory=lambda: f"ACT-{uuid.uuid4().hex[:10].upper()}")
    case_id: str
    actor_id: str
    actor_name: str
    event_type: CaseActivityEventType
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None


class EvidenceRelationshipType(str, Enum):
    """Types of provenance relationships connecting evidence to findings."""
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"
    RELATED_TO = "RELATED_TO"


class EvidenceProvenance(BaseModel):
    """Forensic provenance record tracking how evidence informs decisions."""
    provenance_id: str = Field(default_factory=lambda: f"PRV-{uuid.uuid4().hex[:8].upper()}")
    evidence_id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relationship_type: EvidenceRelationshipType
    derived_factor: Optional[str] = None
    contribution: float = 1.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EnterpriseFraudPostureDriver(BaseModel):
    """Single positive or negative driver influencing enterprise fraud posture."""
    factor_name: str
    impact: str = "POSITIVE"  # 'POSITIVE' (increases posture/safety) or 'NEGATIVE' (increases risk/hazard)
    score_contribution: float
    description: str


class EnterpriseFraudPosture(BaseModel):
    """Executive composite health metric indicating enterprise fraud risk status (0-100)."""
    posture_score: float = Field(..., ge=0.0, le=100.0)
    previous_score: float = 75.0
    score_delta: float = 0.0
    risk_level: RiskLevel
    top_drivers: List[EnterpriseFraudPostureDriver] = Field(default_factory=list)
    positive_drivers: List[str] = Field(default_factory=list)
    negative_drivers: List[str] = Field(default_factory=list)
    summary: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommandCenterSummary(BaseModel):
    """Executive Command Center operational KPIs and active campaign overview."""
    active_investigations: int
    critical_alerts: int
    open_fraud_cases: int
    confirmed_fraud_value: float
    potential_exposure: float
    active_campaigns_count: int
    sla_breach_rate: float
    high_risk_networks_count: int
    top_campaigns: List[Campaign] = Field(default_factory=list)
    posture: EnterpriseFraudPosture


# ---------------------------------------------------------------------------
# API Request / Response Payloads
# ---------------------------------------------------------------------------

class AddCollaboratorRequest(BaseModel):
    user_id: str
    username: str
    role: CollaboratorRole = CollaboratorRole.COLLABORATOR


class AddCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class UpdateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class CampaignUpdateRequest(BaseModel):
    status: Optional[CampaignStatus] = None
    name: Optional[str] = None
    description: Optional[str] = None


class CaseCorrelationResponse(BaseModel):
    case_id: str
    correlations_count: int
    correlations: List[CaseCorrelation]


class CaseEvidenceProvenanceResponse(BaseModel):
    case_id: str
    provenance_count: int
    records: List[EvidenceProvenance]
