"""
FinGraph Forensic Investigation & Search Models.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.models.accounts import AccountSummary
from backend.app.models.alerts import AlertSummary
from detection.src.models import DetectionEvidence, DetectionType, Severity


class SearchResultItem(BaseModel):
    """Generic cross-entity search match."""
    entity_type: str  # "ACCOUNT", "PERSON", "BANK", "TRANSACTION", "ALERT"
    entity_id: str
    title: str
    subtitle: Optional[str] = None
    risk_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResults(BaseModel):
    """Unified search response covering accounts, transactions, and alerts."""
    query: str
    accounts: List[AccountSummary] = Field(default_factory=list)
    alerts: List[AlertSummary] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)


class MoneyTrailStep(BaseModel):
    """Individual hop in a multi-hop money trail."""
    from_account: str
    to_account: str
    transaction_id: str
    amount: float
    currency: str = "USD"
    timestamp: datetime
    scenario_id: Optional[str] = None


class MoneyTrailPath(BaseModel):
    """Complete path discovered between source and destination accounts."""
    path_id: str
    origin: str
    destination: str
    hop_count: int
    total_amount: float
    path_nodes: List[str]
    steps: List[MoneyTrailStep] = Field(default_factory=list)


class MoneyTrailResponse(BaseModel):
    """Complete money trail search result."""
    source_account: str
    destination_account: str
    paths_found_count: int
    paths: List[MoneyTrailPath] = Field(default_factory=list)
    data: Optional[List[MoneyTrailPath]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.data is None:
            self.data = self.paths


class DetectionEvidenceResponse(BaseModel):
    """Raw forensic evidence model."""
    fingerprint: str
    detection_type: DetectionType
    severity: Severity
    confidence: float
    primary_account: str
    evidence: DetectionEvidence
    related_accounts: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    total_amount: Optional[float] = None
    description: str
