"""
FinGraph Advanced Fraud Intelligence, Explainability & Timeline Models.
Provides normalized intelligence representations, rich entity risk profiles,
granular explainable risk factors, chronological timeline events, and alert correlations.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from analytics.src.models import RiskLevel
from backend.app.models.alerts import AlertSummary
from detection.src.models import DetectionType, Severity


class EntityType(str, Enum):
    """Supported entity categories in FinGraph."""
    ACCOUNT = "ACCOUNT"
    PERSON = "PERSON"
    BANK = "BANK"
    DEVICE = "DEVICE"
    MERCHANT = "MERCHANT"
    CARD = "CARD"
    IP = "IP"


class TimelineEventType(str, Enum):
    """Event classifications for investigation chronological timelines."""
    TRANSACTION = "TRANSACTION"
    DETECTOR_MATCH = "DETECTOR_MATCH"
    RISK_SCORE_CHANGE = "RISK_SCORE_CHANGE"
    ALERT_CREATED = "ALERT_CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    ACCOUNT_FROZEN = "ACCOUNT_FROZEN"
    CASE_CREATED = "CASE_CREATED"
    CASE_UPDATED = "CASE_UPDATED"
    INVESTIGATION_NOTE = "INVESTIGATION_NOTE"
    EVIDENCE_ATTACHED = "EVIDENCE_ATTACHED"


class ExplainableRiskFactor(BaseModel):
    """Individual ranked risk factor with evidence grounding."""
    factor_type: str
    description: str
    severity: Severity = Severity.MEDIUM
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    evidence_reference: Optional[str] = None
    value: Optional[Any] = None


class RiskExplanationResponse(BaseModel):
    """Detailed explainable breakdown for elevated entity or alert risk."""
    entity_id: str
    entity_type: EntityType = EntityType.ACCOUNT
    risk_score: float
    risk_level: RiskLevel
    reasons: List[ExplainableRiskFactor] = Field(default_factory=list)
    summary: str


class EntityRiskProfile(BaseModel):
    """Rich multi-dimensional entity risk dossier."""
    entity_id: str
    entity_type: EntityType
    name: Optional[str] = None
    risk_score: float
    risk_level: RiskLevel
    major_risk_factors: List[ExplainableRiskFactor] = Field(default_factory=list)
    detector_hits: List[str] = Field(default_factory=list)
    graph_metrics: Dict[str, Any] = Field(default_factory=dict)
    connected_suspicious_entities: List[Dict[str, Any]] = Field(default_factory=list)
    recent_suspicious_activity: List[Dict[str, Any]] = Field(default_factory=list)
    investigation_history: List[Dict[str, Any]] = Field(default_factory=list)
    is_frozen: bool = False
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InvestigationTimelineEvent(BaseModel):
    """Single chronological forensic event."""
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8].upper()}")
    timestamp: datetime
    event_type: TimelineEventType
    actor: Optional[str] = None
    entity_id: str
    entity_type: EntityType = EntityType.ACCOUNT
    title: str
    description: str
    evidence_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InvestigationTimelineResponse(BaseModel):
    """Chronological event feed response for an entity or case."""
    entity_id: str
    total_events: int
    events: List[InvestigationTimelineEvent] = Field(default_factory=list)


class AlertCorrelation(BaseModel):
    """Cross-alert correlation identifying shared syndicate topologies."""
    alert_id: str
    related_alerts_count: int
    correlated_alerts: List[AlertSummary] = Field(default_factory=list)
    common_entities: List[str] = Field(default_factory=list)
    common_detectors: List[str] = Field(default_factory=list)
    correlation_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    correlation_reason: str


class AlertRecommendationItem(BaseModel):
    """Deterministic next-step investigation recommendation."""
    action_type: str  # "INSPECT_TRAIL", "FREEZE_ACCOUNT", "CREATE_CASE", "REVIEW_COUNTERPARTIES", "ISOLATE_COMMUNITY"
    title: str
    description: str
    priority: Severity = Severity.HIGH
    target_entity: Optional[str] = None
    evidence_summary: str


class AlertRecommendationsResponse(BaseModel):
    """Recommended investigation actions for an alert."""
    alert_id: str
    recommendations: List[AlertRecommendationItem] = Field(default_factory=list)


class InvestigationAnalytics(BaseModel):
    """Aggregate forensic intelligence analytics."""
    cases_by_status: Dict[str, int] = Field(default_factory=dict)
    cases_by_priority: Dict[str, int] = Field(default_factory=dict)
    alerts_by_detector: Dict[str, int] = Field(default_factory=dict)
    alerts_by_severity: Dict[str, int] = Field(default_factory=dict)
    high_risk_entities_count: int = 0
    active_investigators_count: int = 0
    top_suspicious_communities: List[Dict[str, Any]] = Field(default_factory=list)
