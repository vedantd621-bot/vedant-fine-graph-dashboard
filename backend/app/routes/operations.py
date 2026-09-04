"""
FinGraph Operations & Alert Prioritization REST Endpoints.
Provides investigator queue, triage state machine, workload management,
SLA analytics, time-series trends, detector confirmation stats, and unified search.
"""
from datetime import datetime
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

logger = logging.getLogger("FinGraph.OperationsRouter")

from detection.src.models import DetectionType, Severity
from analytics.src.models import RiskLevel
from backend.app.dependencies import get_operations_service
from backend.app.models.common import ApiResponse, PaginatedResponse, PaginationMeta
from backend.app.models.operations import (
    AlertAssignRequest,
    AlertPriorityExplanation,
    AlertTriageRequest,
    BulkAlertAssignRequest,
    BulkAlertTriageRequest,
    BulkOperationResult,
    DetectorPerformanceResponse,
    FraudTrendsResponse,
    OperationsSummary,
    PrioritizedAlert,
    PrioritizedAlertListResponse,
    PriorityLevel,
    SLASummary,
    TriageStatus,
    UnifiedSearchResponse,
    WorkloadListResponse,
)
from backend.app.security.dependencies import (
    get_current_user,
    require_role,
)
from backend.app.security.models import Role, User
from backend.app.services.operations_service import OperationsService

router = APIRouter(prefix="/api/v1/operations", tags=["Operations & Prioritization"])


@router.get(
    "/alerts",
    response_model=ApiResponse[PrioritizedAlertListResponse],
    summary="List all prioritized alerts",
)
def list_prioritized_alerts(
    severity: Optional[Severity] = None,
    status: Optional[TriageStatus] = None,
    detection_type: Optional[DetectionType] = None,
    risk_level: Optional[RiskLevel] = None,
    priority: Optional[PriorityLevel] = None,
    assigned_to: Optional[str] = None,
    network_id: Optional[str] = None,
    case_id: Optional[str] = None,
    search: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("priority_score", pattern="^(priority_score|risk_score|total_amount|time_remaining|severity|created_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    service: OperationsService = Depends(get_operations_service),
):
    """Returns paginated, prioritized operational alerts with SLA and triage status."""
    data, total_items = service.list_queue_alerts(
        severity=severity,
        status=status,
        detection_type=detection_type,
        risk_level=risk_level,
        priority=priority,
        assigned_to=assigned_to,
        network_id=network_id,
        case_id=case_id,
        search=search,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    pagination = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
    return ApiResponse(data=PrioritizedAlertListResponse(data=data, pagination=pagination))


@router.get(
    "/queue",
    response_model=ApiResponse[PrioritizedAlertListResponse],
    summary="Investigator alert queue",
)
def get_investigator_queue(
    assigned_to: Optional[str] = None,
    status: Optional[TriageStatus] = None,
    priority: Optional[PriorityLevel] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: OperationsService = Depends(get_operations_service),
):
    """Returns investigator alert queue filtered by assigned investigator or priority."""
    target_assignee = assigned_to or (current_user.username if current_user.role == Role.INVESTIGATOR else None)
    data, total_items = service.list_queue_alerts(
        status=status,
        priority=priority,
        assigned_to=target_assignee,
        page=page,
        page_size=page_size,
        sort="priority_score",
        order="desc",
    )
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    pagination = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
    return ApiResponse(data=PrioritizedAlertListResponse(data=data, pagination=pagination))


@router.get(
    "/alerts/{alert_id}/priority-explanation",
    response_model=ApiResponse[AlertPriorityExplanation],
    summary="Explain alert priority score",
)
def get_alert_priority_explanation(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    service: OperationsService = Depends(get_operations_service),
):
    """Returns mathematical and forensic factor contributions for an alert priority score."""
    explanation = service.get_alert_priority_explanation(alert_id)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return ApiResponse(data=explanation)


@router.post(
    "/alerts/{alert_id}/triage",
    response_model=ApiResponse[PrioritizedAlert],
    summary="Transition alert triage status",
)
def triage_alert(
    alert_id: str,
    payload: AlertTriageRequest,
    request: Request,
    current_user: User = Depends(require_role([Role.INVESTIGATOR, Role.ADMIN])),
    service: OperationsService = Depends(get_operations_service),
):
    """Transitions an alert through the 7-state triage state machine with audit logging."""
    request_id = getattr(request.state, "request_id", None)
    try:
        updated = service.triage_alert(
            alert_id=alert_id,
            new_status=payload.new_status,
            user_id=current_user.user_id,
            username=current_user.username,
            notes=payload.notes,
            escalation_reason=payload.escalation_reason,
            request_id=request_id,
        )
        return ApiResponse(data=updated)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/alerts/{alert_id}/assign",
    response_model=ApiResponse[PrioritizedAlert],
    summary="Assign or reassign alert investigator",
)
def assign_alert(
    alert_id: str,
    payload: AlertAssignRequest,
    request: Request,
    current_user: User = Depends(require_role([Role.INVESTIGATOR, Role.ADMIN])),
    service: OperationsService = Depends(get_operations_service),
):
    """Assigns or reassigns an investigator to an alert."""
    request_id = getattr(request.state, "request_id", None)
    try:
        updated = service.assign_alert(
            alert_id=alert_id,
            assigned_to=payload.assigned_to,
            user_id=current_user.user_id,
            username=current_user.username,
            notes=payload.notes,
            request_id=request_id,
        )
        return ApiResponse(data=updated)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/alerts/{alert_id}/unassign",
    response_model=ApiResponse[PrioritizedAlert],
    summary="Unassign investigator from alert",
)
def unassign_alert(
    alert_id: str,
    request: Request,
    current_user: User = Depends(require_role([Role.INVESTIGATOR, Role.ADMIN])),
    service: OperationsService = Depends(get_operations_service),
):
    """Unassigns an investigator from an alert."""
    request_id = getattr(request.state, "request_id", None)
    try:
        updated = service.unassign_alert(
            alert_id=alert_id,
            user_id=current_user.user_id,
            username=current_user.username,
            request_id=request_id,
        )
        return ApiResponse(data=updated)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/alerts/bulk-triage",
    response_model=ApiResponse[BulkOperationResult],
    summary="Bulk triage multiple alerts",
)
def bulk_triage_alerts(
    payload: BulkAlertTriageRequest,
    request: Request,
    current_user: User = Depends(require_role([Role.INVESTIGATOR, Role.ADMIN])),
    service: OperationsService = Depends(get_operations_service),
):
    """Performs bounded batch triage across up to 50 alerts."""
    request_id = getattr(request.state, "request_id", None)
    result = service.bulk_triage_alerts(
        alert_ids=payload.alert_ids,
        new_status=payload.new_status,
        user_id=current_user.user_id,
        username=current_user.username,
        notes=payload.notes,
        request_id=request_id,
    )
    return ApiResponse(data=result)


@router.post(
    "/alerts/bulk-assign",
    response_model=ApiResponse[BulkOperationResult],
    summary="Bulk assign multiple alerts",
)
def bulk_assign_alerts(
    payload: BulkAlertAssignRequest,
    request: Request,
    current_user: User = Depends(require_role([Role.INVESTIGATOR, Role.ADMIN])),
    service: OperationsService = Depends(get_operations_service),
):
    """Performs bounded batch assignment across up to 50 alerts."""
    request_id = getattr(request.state, "request_id", None)
    result = service.bulk_assign_alerts(
        alert_ids=payload.alert_ids,
        assigned_to=payload.assigned_to,
        user_id=current_user.user_id,
        username=current_user.username,
        notes=payload.notes,
        request_id=request_id,
    )
    return ApiResponse(data=result)


@router.get(
    "/workload",
    response_model=ApiResponse[WorkloadListResponse],
    summary="Investigator workload capacity analytics",
)
def get_investigator_workload(
    investigator_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: OperationsService = Depends(get_operations_service),
):
    """Returns workload, active case count, and resolution velocity per investigator."""
    workload = service.get_investigator_workloads(investigator_id=investigator_id)
    return ApiResponse(data=workload)


@router.get(
    "/sla",
    response_model=ApiResponse[SLASummary],
    summary="SLA compliance and deadline tracking",
)
def get_sla_compliance(
    current_user: User = Depends(get_current_user),
    service: OperationsService = Depends(get_operations_service),
):
    """Returns SLA compliance rates, at-risk alerts, and breached items."""
    sla_data = service.get_sla_summary()
    return ApiResponse(data=sla_data)


@router.get(
    "/trends",
    response_model=ApiResponse[FraudTrendsResponse],
    summary="Time-series fraud trends analytics",
)
def get_fraud_trends(
    interval: str = Query("hourly", pattern="^(hourly|daily)$"),
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    service: OperationsService = Depends(get_operations_service),
):
    """Returns time-series alert volumes, fraud values, and status breakdowns."""
    trends = service.get_fraud_trends(interval=interval, days=days)
    return ApiResponse(data=trends)


@router.get(
    "/detectors",
    response_model=ApiResponse[DetectorPerformanceResponse],
    summary="Detector operational confirmation metrics",
)
def get_detector_performance(
    current_user: User = Depends(get_current_user),
    service: OperationsService = Depends(get_operations_service),
):
    """Returns operational confirmation rate and activity per fraud detector."""
    metrics = service.get_detector_performance()
    return ApiResponse(data=metrics)


@router.get(
    "/summary",
    response_model=ApiResponse[OperationsSummary],
    summary="Executive operations KPI summary",
)
def get_operations_summary(
    current_user: User = Depends(get_current_user),
    service: OperationsService = Depends(get_operations_service),
):
    """Returns executive overview KPIs for fraud operations."""
    summary_data = service.get_operations_summary()
    return ApiResponse(data=summary_data)


@router.get(
    "/search",
    response_model=ApiResponse[UnifiedSearchResponse],
    summary="Multi-entity unified investigation search",
)
def unified_search(
    q: str = Query(..., min_length=1, max_length=100),
    entity_types: Optional[List[str]] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    current_user: User = Depends(get_current_user),
    service: OperationsService = Depends(get_operations_service),
):
    """Searches across alerts, cases, accounts, networks, and investigators."""
    results = service.unified_search(
        query=q,
        entity_types=entity_types,
        limit=limit,
        page=page,
    )
    return ApiResponse(data=results)
