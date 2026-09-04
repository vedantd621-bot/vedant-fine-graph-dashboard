"""
FinGraph Fraud Network & Syndicate Data Models (Pydantic V2).
Defines structured entities, roles, risk contributions, evidence, and timelines for discovered fraud networks.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from analytics.src.models import RiskLevel
from detection.src.models import Severity
from backend.app.models.common import PaginationMeta


class NetworkType(str, Enum):
    """Classifications of discovered fraud network topologies."""
    CIRCULAR_RING = "CIRCULAR_RING"
    FAN_IN_CONSOLIDATION = "FAN_IN_CONSOLIDATION"
    FAN_OUT_DISPERSION = "FAN_OUT_DISPERSION"
    LAYERED_CHAIN = "LAYERED_CHAIN"
    COMMUNITY_SYNDICATE = "COMMUNITY_SYNDICATE"
    SHARED_INFRASTRUCTURE = "SHARED_INFRASTRUCTURE"


class NetworkMemberRole(str, Enum):
    """Functional role of an account within a fraud network."""
    ORIGINATOR = "ORIGINATOR"
    AGGREGATOR = "AGGREGATOR"
    DISPERSER = "DISPERSER"
    MULE = "MULE"
    INTERMEDIARY = "INTERMEDIARY"
    MEMBER = "MEMBER"


class FraudNetworkMember(BaseModel):
    """Constituent account entity within a discovered fraud network."""
    account_id: str
    role: NetworkMemberRole = NetworkMemberRole.MEMBER
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    in_degree: int = 0
    out_degree: int = 0
    total_degree: int = 0
    pagerank: float = 0.0
    total_volume: float = 0.0
    is_frozen: bool = False
    joined_at: Optional[datetime] = None


class NetworkRiskFactor(BaseModel):
    """Explainable risk factor contributing to network-level risk score."""
    factor_name: str
    description: str
    weight: float
    raw_value: Any
    contribution: float
    evidence: Dict[str, Any] = Field(default_factory=dict)


class NetworkEvidence(BaseModel):
    """Traceable forensic evidence item grounding a discovered fraud network."""
    evidence_id: str
    source_type: str  # "DETECTOR", "TOPOLOGY", "COMMUNITY", "TRANSACTION_HUB"
    description: str
    entity_ids: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    detector_fingerprints: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NetworkTimelineEvent(BaseModel):
    """Chronological event in the lifecycle of a fraud network."""
    timestamp: datetime
    event_type: str  # "TRANSACTION", "DETECTOR_MATCH", "ALERT_CREATED", "RISK_ELEVATED", "CASE_LINKED"
    entity_id: str
    title: str
    description: str
    evidence_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FraudNetwork(BaseModel):
    """Complete fraud network dossier with members, risk factors, and evidence."""
    network_id: str
    name: str
    network_type: NetworkType
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    member_count: int = 0
    transaction_count: int = 0
    total_volume: float = 0.0
    detector_count: int = 0
    community_id: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    members: List[FraudNetworkMember] = Field(default_factory=list)
    risk_factors: List[NetworkRiskFactor] = Field(default_factory=list)
    evidence: List[NetworkEvidence] = Field(default_factory=list)
    linked_cases: List[str] = Field(default_factory=list)
    linked_alerts: List[str] = Field(default_factory=list)


class NetworkSummary(BaseModel):
    """Compact summary for fraud network catalog views."""
    network_id: str
    name: str
    network_type: NetworkType
    risk_score: float
    risk_level: RiskLevel
    member_count: int
    transaction_count: int
    total_volume: float
    detector_count: int
    community_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    linked_cases_count: int = 0
    linked_alerts_count: int = 0


class NetworkListResponse(BaseModel):
    """Paginated list of discovered fraud networks."""
    data: List[NetworkSummary]
    pagination: PaginationMeta


class NetworkDetail(BaseModel):
    """Comprehensive fraud network detail response."""
    network: FraudNetwork
    recent_timeline: List[NetworkTimelineEvent] = Field(default_factory=list)


class NetworkMemberResponse(BaseModel):
    """List of member accounts within a fraud network."""
    network_id: str
    members: List[FraudNetworkMember]
    total_members: int


class NetworkEvidenceResponse(BaseModel):
    """Forensic evidence items associated with a fraud network."""
    network_id: str
    evidence: List[NetworkEvidence]
    total_items: int


class NetworkRiskExplanationResponse(BaseModel):
    """Explainable breakdown of factors contributing to network risk score."""
    network_id: str
    risk_score: float
    risk_level: RiskLevel
    summary: str
    factors: List[NetworkRiskFactor]


class NetworkCreateCaseRequest(BaseModel):
    """Request payload to promote a fraud network directly into an investigation case."""
    title: Optional[str] = None
    priority: Optional[str] = "HIGH"
    initial_notes: Optional[str] = None
