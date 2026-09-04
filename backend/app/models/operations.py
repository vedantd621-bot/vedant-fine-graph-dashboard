"""
FinGraph Operations, Alert Prioritization, Triage & SLA Models.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from detection.src.models import AlertStatus, DetectionEvidence, DetectionType, Severity
from analytics.src.models import RiskLevel
from backend.app.models.common import PaginationMeta


class PriorityLevel(str, Enum):
    """Discrete operational urgency priority tiers."""
    P0_CRITICAL = "P0_CRITICAL"
    P1_HIGH = "P1_HIGH"
    P2_MEDIUM = "P2_MEDIUM"
    P3_LOW = "P3_LOW"


class TriageStatus(str, Enum):
    """7-state investigative triage lifecycle states."""
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    ESCALATED = "ESCALATED"
    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    CLOSED = "CLOSED"


class SLAStatus(str, Enum):
    """SLA compliance tracking status."""
    WITHIN_SLA = "WITHIN_SLA"
    AT_RISK = "AT_RISK"
    BREACHED = "BREACHED"
    RESOLVED = "RESOLVED"


class PriorityFactor(BaseModel):
    """Individual explainable factor contributing to priority score."""
    factor_name: str
    weight: float
    raw_value: float
    contribution: float
    evidence: str


class AlertPriorityExplanation(BaseModel):
    """Transparent explainability payload for alert priority."""
    alert_id: str
    priority_score: float
    priority_level: PriorityLevel
    factors: List[PriorityFactor]
    summary: str


class PrioritizedAlert(BaseModel):
    """Enriched operational alert with priority, triage state, and SLA countdown."""
    alert_id: str
    detection_type: DetectionType
    severity: Severity
    confidence: float
    primary_account: str
    related_accounts: List[str] = Field(default_factory=list)
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    priority_score: float
    priority_level: PriorityLevel
    triage_status: TriageStatus = TriageStatus.NEW
    assigned_investigator: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    sla_deadline: datetime
    sla_status: SLAStatus
    time_remaining_minutes: float
    description: str
    total_amount: Optional[float] = None
    currency: str = "USD"
    duplicate_group_id: Optional[str] = None
    correlation_group_id: Optional[str] = None
    network_id: Optional[str] = None
    case_id: Optional[str] = None


class PrioritizedAlertListResponse(BaseModel):
    """Paginated list of prioritized operational alerts."""
    data: List[PrioritizedAlert]
    pagination: PaginationMeta


class AlertTriageRequest(BaseModel):
    """Payload for transitioning an alert through triage states."""
    new_status: TriageStatus
    notes: Optional[str] = None
    escalation_reason: Optional[str] = None


class AlertAssignRequest(BaseModel):
    """Payload for assigning or reassigning an alert to an investigator."""
    assigned_to: str
    notes: Optional[str] = None


class BulkAlertTriageRequest(BaseModel):
    """Payload for batch triaging multiple alerts safely."""
    alert_ids: List[str] = Field(..., min_length=1, max_length=50)
    new_status: TriageStatus
    notes: Optional[str] = None


class BulkAlertAssignRequest(BaseModel):
    """Payload for batch assigning multiple alerts to an investigator."""
    alert_ids: List[str] = Field(..., min_length=1, max_length=50)
    assigned_to: str
    notes: Optional[str] = None


class BulkOperationResult(BaseModel):
    """Summary result of a batch operation."""
    success_count: int
    failed_count: int
    processed_ids: List[str]
    errors: Dict[str, str] = Field(default_factory=dict)


class InvestigatorWorkload(BaseModel):
    """Operational capacity and investigation velocity metrics for an investigator."""
    investigator_id: str
    username: str
    assigned_alerts: int
    open_cases: int
    critical_alerts: int
    overdue_alerts: int
    avg_resolution_hours: float
    alerts_resolved: int
    false_positive_rate: float
    active_investigations: int


class WorkloadListResponse(BaseModel):
    """List of all active investigator workloads."""
    investigators: List[InvestigatorWorkload]
    total_assigned_alerts: int
    total_open_cases: int


class SLAItem(BaseModel):
    """Item tracking SLA deadline and status."""
    alert_id: str
    priority_level: PriorityLevel
    triage_status: TriageStatus
    created_at: datetime
    sla_deadline: datetime
    sla_status: SLAStatus
    time_remaining_minutes: float
    assigned_investigator: Optional[str] = None


class SLASummary(BaseModel):
    """Executive and operational summary of SLA compliance."""
    total_tracked: int
    within_sla_count: int
    at_risk_count: int
    breached_count: int
    compliance_rate: float  # Percentage within SLA
    items: List[SLAItem] = Field(default_factory=list)


class OperationsSummary(BaseModel):
    """Executive overview KPIs for fraud operations."""
    alerts_today: int
    critical_alerts: int
    confirmed_fraud: int
    false_positives: int
    open_investigations: int
    sla_compliance_rate: float
    avg_resolution_hours: float
    total_fraud_value_prevented: float
    currency: str = "USD"
    top_detectors: List[Dict[str, Any]] = Field(default_factory=list)
    active_networks_count: int


class FraudTrendPoint(BaseModel):
    """Time-series observation bucket."""
    timestamp: datetime
    alert_count: int
    critical_count: int
    confirmed_fraud_count: int
    false_positive_count: int
    fraud_amount: float


class FraudTrendsResponse(BaseModel):
    """Time-series trend analytics payload."""
    interval: str  # "hourly", "daily"
    points: List[FraudTrendPoint]
    total_alerts: int
    total_amount: float


class DetectorPerformanceMetrics(BaseModel):
    """Operational confirmation and activity metrics for a single detector."""
    detection_type: DetectionType
    alert_count: int
    confirmed_fraud_count: int
    false_positive_count: int
    operational_confirmation_rate: float
    avg_risk_score: float
    total_amount: float


class DetectorPerformanceResponse(BaseModel):
    """Collection of operational detector performance stats."""
    detectors: List[DetectorPerformanceMetrics]
    disclaimer: str = "Operational confirmation rates reflect investigator decisions and are distinct from ML precision/recall."


class SearchResultItem(BaseModel):
    """Result item across unified search entities."""
    entity_type: str  # "ALERT", "CASE", "ACCOUNT", "TRANSACTION", "NETWORK", "INVESTIGATOR"
    entity_id: str
    title: str
    subtitle: Optional[str] = None
    severity_or_status: Optional[str] = None
    risk_or_priority: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UnifiedSearchResponse(BaseModel):
    """Response payload for multi-entity investigation search."""
    query: str
    total_matches: int
    results: List[SearchResultItem]
