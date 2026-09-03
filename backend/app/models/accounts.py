"""
FinGraph Account REST Models.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals


class AccountSummary(BaseModel):
    """Compact account entity for catalogs and tables."""
    account_id: str
    account_type: str = "checking"
    bank_id: Optional[str] = None
    bank_name: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    total_degree: int = 0
    in_degree: int = 0
    out_degree: int = 0
    pagerank: float = 0.0
    louvain_community_id: Optional[int] = None
    wcc_id: Optional[int] = None
    total_volume: float = 0.0
    is_frozen: bool = False
    updated_at: Optional[datetime] = None


class AccountDetail(BaseModel):
    """Complete account dossier with GDS features, ownership, and risk justification."""
    account_id: str
    account_type: str = "checking"
    bank_id: Optional[str] = None
    bank_name: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    model_version: str = "rule-gds-v1"
    calculated_at: Optional[datetime] = None
    features: GraphFeatures
    rule_signals: RuleSignals
    risk_reasons: List[str] = Field(default_factory=list)
    is_frozen: bool = False
    frozen_at: Optional[datetime] = None


class AccountTransactionItem(BaseModel):
    """Transaction item associated with an account."""
    transaction_id: str
    direction: str  # "INCOMING" or "OUTGOING"
    counterparty: str
    counterparty_name: Optional[str] = None
    amount: float
    currency: str = "USD"
    timestamp: datetime
    transaction_type: str = "transfer"
    scenario_id: Optional[str] = None
    channel: Optional[str] = None


class AccountFreezeRequest(BaseModel):
    """Request payload to simulate freezing or unfreezing an account."""
    freeze: bool = True
    reason: Optional[str] = "Simulated fraud containment freeze"


class AccountFreezeResponse(BaseModel):
    """Response payload confirming account freeze state."""
    account_id: str
    is_frozen: bool
    action: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
