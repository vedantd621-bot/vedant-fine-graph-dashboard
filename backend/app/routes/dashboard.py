"""
FinGraph Executive Dashboard Endpoints.
Aggregates network-level KPIs, risk distribution histograms, alert trends, and priority investigation targets.
Protected by Authentication and RBAC.
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from backend.app.dependencies import get_dashboard_service
from backend.app.models.accounts import AccountSummary
from backend.app.models.dashboard import AlertTrendPoint, DashboardSummary, RiskDistribution
from backend.app.security.dependencies import require_analyst
from backend.app.security.models import User
from backend.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user: User = Depends(require_analyst),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Retrieves high-level executive fraud intelligence metrics and active case counts."""
    return service.get_dashboard_summary()


@router.get("/risk-distribution", response_model=RiskDistribution)
def get_risk_distribution(
    current_user: User = Depends(require_analyst),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Returns histogram distribution of account risk across LOW, MEDIUM, HIGH, and CRITICAL bands."""
    return service.get_risk_distribution()


@router.get("/alert-trend", response_model=List[AlertTrendPoint])
def get_alert_trend(
    current_user: User = Depends(require_analyst),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Returns alert generation counts grouped by day."""
    return service.get_alert_trend()


@router.get("/top-risk-accounts", response_model=List[AccountSummary])
def get_top_risk_accounts(
    limit: int = Query(5, ge=1, le=50, description="Number of top-risk accounts to retrieve"),
    current_user: User = Depends(require_analyst),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Returns top prioritized accounts ordered by composite risk score."""
    return service.get_top_risk_accounts(limit=limit)
