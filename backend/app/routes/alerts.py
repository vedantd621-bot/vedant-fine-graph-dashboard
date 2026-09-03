"""
FinGraph Alert REST Endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from detection.src.models import AlertStatus, DetectionType, Severity
from analytics.src.models import RiskLevel
from backend.app.dependencies import (
    get_detection_engine,
    get_neo4j_client,
    get_risk_engine,
)
from backend.app.models.alerts import (
    AlertDetail,
    AlertStatusUpdateRequest,
    AlertSummary,
)
from backend.app.models.common import ApiResponse, PaginatedResponse, PaginationMeta
from backend.app.services.alert_service import AlertService

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


def get_alert_service(
    client=Depends(get_neo4j_client),
    det_eng=Depends(get_detection_engine),
    risk_eng=Depends(get_risk_engine),
) -> AlertService:
    return AlertService(client=client, detection_engine=det_eng, risk_engine=risk_eng)


@router.get("", response_model=PaginatedResponse[AlertSummary])
def list_alerts(
    severity: Optional[Severity] = Query(None, description="Filter by severity level"),
    status: Optional[AlertStatus] = Query(None, description="Filter by investigation status"),
    detection_type: Optional[DetectionType] = Query(None, description="Filter by pattern type"),
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by account risk level"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at", description="Sort field: created_at, risk_score, severity"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    service: AlertService = Depends(get_alert_service),
):
    """Lists all active and historical fraud alerts with pagination and filtering."""
    items, total = service.list_alerts(
        severity=severity,
        status=status,
        detection_type=detection_type,
        risk_level=risk_level,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return PaginatedResponse(data=items, pagination=meta)


@router.get("/{alert_id}", response_model=ApiResponse[AlertDetail])
def get_alert_detail(
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
):
    """Retrieves full investigative details and forensic evidence for a specific alert."""
    detail = service.get_alert_by_id(alert_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert '{alert_id}' was not found."},
        )
    return ApiResponse(data=detail)


@router.patch("/{alert_id}", response_model=ApiResponse[AlertDetail])
def update_alert_status(
    alert_id: str,
    payload: AlertStatusUpdateRequest,
    service: AlertService = Depends(get_alert_service),
):
    """Updates the investigation lifecycle status of an alert (OPEN, INVESTIGATING, RESOLVED, DISMISSED)."""
    updated = service.update_alert_status(alert_id, payload.status)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert '{alert_id}' was not found."},
        )
    return ApiResponse(data=updated)
