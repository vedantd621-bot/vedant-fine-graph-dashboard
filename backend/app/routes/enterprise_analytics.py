"""
Enterprise Analytics REST Endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from backend.app.enterprise_analytics.models import (
    DetectionKPIs, EnterpriseKPIBundle, ExecutiveFraudPosture, ExecutiveInsight,
    FinancialKPIs, FraudKPIs, FraudTrendPoint, KPIAnomaly, NetworkKPIs,
    OperationsKPIs, TrendWindow
)
from backend.app.enterprise_analytics.service import (
    EnterpriseAnalyticsService, get_enterprise_analytics_service
)
from backend.app.security.dependencies import require_analyst
from backend.app.security.models import User

router = APIRouter(prefix="/api/v1/analytics", tags=["enterprise-analytics"])


@router.get("/kpis", response_model=EnterpriseKPIBundle)
def get_all_kpis(
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve full enterprise KPI bundle with all dimensions and posture."""
    return service.get_kpi_bundle(current_user.tenant_id)


@router.get("/fraud-kpis", response_model=FraudKPIs)
def get_fraud_kpis(
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve fraud-specific KPIs."""
    return service.get_fraud_kpis(current_user.tenant_id)


@router.get("/financial-kpis", response_model=FinancialKPIs)
def get_financial_kpis(
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve financial exposure, loss prevention, and recovery KPIs."""
    return service.get_financial_kpis(current_user.tenant_id)


@router.get("/operations-kpis", response_model=OperationsKPIs)
def get_operations_kpis(
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve operational queue depth, backlog, and SLA metrics."""
    return service.get_operations_kpis(current_user.tenant_id)


@router.get("/detection-kpis", response_model=DetectionKPIs)
def get_detection_kpis(
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve detector precision proxy, hit rates, and rule drift."""
    return service.get_detection_kpis(current_user.tenant_id)


@router.get("/network-kpis", response_model=NetworkKPIs)
def get_network_kpis(
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve graph intelligence network and campaign analytics."""
    return service.get_network_kpis(current_user.tenant_id)


@router.get("/posture", response_model=ExecutiveFraudPosture)
def get_executive_posture(
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve executive composite fraud posture score and driver breakdown."""
    return service.get_executive_posture(current_user.tenant_id)


@router.get("/insights", response_model=List[ExecutiveInsight])
def get_executive_insights(
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve evidence-attributed executive insights."""
    return service.get_executive_insights(current_user.tenant_id)


@router.get("/trends", response_model=List[FraudTrendPoint])
def get_fraud_trends(
    window: TrendWindow = Query(TrendWindow.DAILY),
    periods: int = Query(14, ge=3, le=90),
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve time-series fraud trend points with data quality metadata."""
    return service.get_fraud_trends(current_user.tenant_id, window=window, periods=periods)


@router.get("/anomalies", response_model=List[KPIAnomaly])
def get_kpi_anomalies(
    current_user: User = Depends(require_analyst),
    service: EnterpriseAnalyticsService = Depends(get_enterprise_analytics_service),
):
    """Retrieve statistical KPI deviations and operational anomalies."""
    return service.get_kpi_anomalies(current_user.tenant_id)
