"""
FinGraph Dashboard Summary & Analytics Aggregate Models.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from analytics.src.models import RiskLevel
from backend.app.models.accounts import AccountSummary
from backend.app.models.alerts import AlertSummary


class DashboardSummary(BaseModel):
    """Core KPI metrics for the executive and operations fraud dashboard."""
    total_accounts: int = 0
    total_transactions: int = 0
    open_alerts: int = 0
    investigating_alerts: int = 0
    resolved_alerts: int = 0
    high_risk_accounts: int = 0
    critical_risk_accounts: int = 0
    total_transaction_volume: float = 0.0
    currency: str = "USD"
    updated_at: datetime


class RiskDistribution(BaseModel):
    """Categorical count breakdown across risk bands."""
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0
    total: int = 0
    total_accounts: Optional[int] = None

    def model_post_init(self, __context: Any) -> None:
        if self.total_accounts is None:
            self.total_accounts = self.total


class AlertTrendPoint(BaseModel):
    """Time-series data point for alert volume charts."""
    timestamp: str
    count: int = 0
    severity_breakdown: Dict[str, int] = Field(default_factory=dict)
