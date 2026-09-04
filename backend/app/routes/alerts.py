"""
FinGraph Alert API Endpoints.
Provides alert discovery, multi-filter search, forensic detail dossier retrieval, and investigation status transitions.
Protected by Authentication and RBAC.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from analytics.src.models import RiskLevel
from backend.app.dependencies import get_alert_service
from backend.app.models.alerts import AlertDetail, AlertListResponse, AlertStatusUpdateRequest, AlertSummary
from backend.app.models.common import PaginationMeta
from backend.app.security.audit import AuditService, get_audit_service
from backend.app.security.dependencies import require_analyst, require_investigator
from backend.app.security.models import User
from backend.app.services.alert_service import AlertService
from detection.src.models import AlertStatus, DetectionType, Severity

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

# Legal investigation state transitions
ALLOWED_TRANSITIONS = {
    AlertStatus.OPEN: {AlertStatus.INVESTIGATING, AlertStatus.DISMISSED, AlertStatus.RESOLVED},
    AlertStatus.INVESTIGATING: {AlertStatus.RESOLVED, AlertStatus.DISMISSED},
    AlertStatus.RESOLVED: {AlertStatus.INVESTIGATING},  # Reopen
    AlertStatus.DISMISSED: {AlertStatus.INVESTIGATING},  # Reopen
}


@router.get("", response_model=AlertListResponse)
def list_alerts(
    severity: Optional[Severity] = Query(None, description="Filter by alert severity"),
    status_filter: Optional[AlertStatus] = Query(None, alias="status", description="Filter by investigation status"),
    detection_type: Optional[DetectionType] = Query(None, description="Filter by fraud pattern type"),
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by primary account risk level"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query("created_at", description="Field to sort by (created_at, risk_score, severity)"),
    order: str = Query("desc", description="Sort order (asc, desc)"),
    current_user: User = Depends(require_analyst),
    service: AlertService = Depends(get_alert_service),
):
    """Returns paginated fraud alerts with multi-dimensional filtering."""
    items, total = service.list_alerts(
        severity=severity,
        status=status_filter,
        detection_type=detection_type,
        risk_level=risk_level,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return AlertListResponse(
        data=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert_detail(
    alert_id: str,
    current_user: User = Depends(require_analyst),
    service: AlertService = Depends(get_alert_service),
):
    """Retrieves full forensic evidence dossier for an alert."""
    detail = service.get_alert_by_id(alert_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert '{alert_id}' not found."},
        )
    return detail


@router.patch("/{alert_id}", response_model=AlertDetail)
def update_alert_status(
    alert_id: str,
    update_req: AlertStatusUpdateRequest,
    current_user: User = Depends(require_investigator),
    service: AlertService = Depends(get_alert_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Updates investigation lifecycle status for an alert (INVESTIGATOR or ADMIN only)."""
    current_detail = service.get_alert_by_id(alert_id)
    if not current_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert '{alert_id}' not found."},
        )

    # State Machine Validation
    current_status = current_detail.status
    new_status = update_req.status
    valid_next_states = ALLOWED_TRANSITIONS.get(current_status, set())

    if new_status != current_status and new_status not in valid_next_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_STATE_TRANSITION",
                "message": f"Cannot transition alert from '{current_status.value}' to '{new_status.value}'. Allowed: {[s.value for s in valid_next_states]}",
            },
        )

    updated = service.update_alert_status(alert_id, update_req.status)

    # Record in audit trail
    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="ALERT_STATUS_UPDATE",
        resource_type="ALERT",
        resource_id=alert_id,
        old_value=current_status.value,
        new_value=new_status.value,
    )

    return updated
