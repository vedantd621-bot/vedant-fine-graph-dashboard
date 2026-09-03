"""
FinGraph Forensic Investigation & Search Models.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.models.accounts import AccountSummary
from backend.app.models.alerts import AlertSummary


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
