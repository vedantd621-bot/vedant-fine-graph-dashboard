"""
FinGraph Executive & Operations Dashboard Endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from backend.app.dependencies import (
    get_detection_engine,
    get_neo4j_client,
    get_risk_engine,
)
from backend.app.models.accounts import AccountSummary
from backend.app.models.common import ApiResponse
from backend.app.models.dashboard import (
    AlertTrendPoint,
    DashboardSummary,
    RiskDistribution,
)
from backend.app.services.account_service import AccountService
from backend.app.services.alert_service import AlertService
from backend.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


def get_dashboard_service(
    client=Depends(get_neo4j_client),
    det_eng=Depends(get_detection_engine),
    risk_eng=Depends(get_risk_engine),
) -> DashboardService:
    acc_svc = AccountService(client=client, risk_engine=risk_eng)
    alt_svc = AlertService(client=client, detection_engine=det_eng, risk_engine=risk_eng)
    return DashboardService(client=client, account_service=acc_svc, alert_service=alt_svc)


@router.get("/summary", response_model=ApiResponse[DashboardSummary])
def get_dashboard_summary(
    service: DashboardService = Depends(get_dashboard_service),
):
    """Retrieves executive summary KPIs (total accounts, open alerts, critical risks, transacted volume)."""
    summary = service.get_summary()
    return ApiResponse(data=summary)


@router.get("/risk-distribution", response_model=ApiResponse[RiskDistribution])
def get_risk_distribution(
    service: DashboardService = Depends(get_dashboard_service),
):
    """Retrieves account population breakdown across LOW, MEDIUM, HIGH, and CRITICAL risk levels."""
    dist = service.get_risk_distribution()
    return ApiResponse(data=dist)


@router.get("/alert-trend", response_model=ApiResponse[List[AlertTrendPoint]])
def get_alert_trends(
    service: DashboardService = Depends(get_dashboard_service),
):
    """Retrieves chronological trend of generated alerts with severity breakdowns."""
    points = service.get_alert_trends()
    return ApiResponse(data=points)


@router.get("/top-risk-accounts", response_model=ApiResponse[List[AccountSummary]])
def get_top_risk_accounts(
    limit: int = Query(10, ge=1, le=50),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Retrieves top high-priority accounts sorted by calculated composite risk score."""
    top_accounts = service.get_top_risk_accounts(limit=limit)
    return ApiResponse(data=top_accounts)
