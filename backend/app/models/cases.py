"""
FinGraph Case Management & Forensic Evidence Models.
Supports full case lifecycle, investigator assignment, note feeds,
cryptographic evidence registry, and account/alert associations.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class CaseStatus(str, Enum):
    """Investigation lifecycle statuses for cases."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CasePriority(str, Enum):
    """Urgency / Severity levels for cases."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceType(str, Enum):
    """Supported classifications of forensic evidence."""
    TRANSACTION = "TRANSACTION"
    ACCOUNT = "ACCOUNT"
    GRAPH_PATH = "GRAPH_PATH"
    DETECTOR_RESULT = "DETECTOR_RESULT"
    NOTE = "NOTE"
    RISK_FACTOR = "RISK_FACTOR"
    EXTERNAL = "EXTERNAL"


class InvestigationNote(BaseModel):
    """Individual investigator note attached to a case."""
    note_id: str = Field(default_factory=lambda: f"NOTE-{uuid.uuid4().hex[:8].upper()}")
    author_id: str
    author_name: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceItem(BaseModel):
    """Forensic evidence item with cryptographic integrity metadata."""
    evidence_id: str = Field(default_factory=lambda: f"EVD-{uuid.uuid4().hex[:8].upper()}")
    case_id: Optional[str] = None
    type: EvidenceType
    source: str
    related_entity: str
    title: str
    description: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    integrity_hash: Optional[str] = None


class InvestigationCase(BaseModel):
    """Complete investigation case record."""
    case_id: str = Field(default_factory=lambda: f"CASE-{uuid.uuid4().hex[:8].upper()}")
    title: str
    description: str
    priority: CasePriority = CasePriority.MEDIUM
    status: CaseStatus = CaseStatus.OPEN
    assigned_investigator: Optional[str] = None
    linked_alerts: List[str] = Field(default_factory=list)
    linked_accounts: List[str] = Field(default_factory=list)
    linked_transactions: List[str] = Field(default_factory=list)
    notes: List[InvestigationNote] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str


class InvestigationCaseSummary(BaseModel):
    """Compact summary for case catalog and listings."""
    case_id: str
    title: str
    priority: CasePriority
    status: CaseStatus
    assigned_investigator: Optional[str] = None
    alerts_count: int = 0
    accounts_count: int = 0
    notes_count: int = 0
    evidence_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: str


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------

class CaseCreateRequest(BaseModel):
    """Payload for initiating a new investigation case."""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=2000)
    priority: CasePriority = CasePriority.MEDIUM
    assigned_investigator: Optional[str] = None
    linked_alerts: List[str] = Field(default_factory=list)
    linked_accounts: List[str] = Field(default_factory=list)
    linked_transactions: List[str] = Field(default_factory=list)


class CaseUpdateRequest(BaseModel):
    """Payload for modifying case status, priority, or metadata."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=5, max_length=2000)
    priority: Optional[CasePriority] = None
    status: Optional[CaseStatus] = None


class CaseAssignRequest(BaseModel):
    """Payload for reassigning investigator on a case."""
    assigned_investigator: str


class CaseNoteCreateRequest(BaseModel):
    """Payload for posting a note on a case."""
    content: str = Field(..., min_length=1, max_length=4000)


class EvidenceCreateRequest(BaseModel):
    """Payload for registering a new forensic evidence item."""
    type: EvidenceType
    source: str
    related_entity: str
    title: str
    description: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class CaseLinkAlertRequest(BaseModel):
    """Payload for associating an alert with a case."""
    alert_id: str


class CaseLinkAccountRequest(BaseModel):
    """Payload for associating an account with a case."""
    account_id: str


class CaseListResponse(BaseModel):
    """Paginated list of investigation cases."""
    data: List[InvestigationCaseSummary]
    total_items: int
    page: int
    page_size: int
    total_pages: int
