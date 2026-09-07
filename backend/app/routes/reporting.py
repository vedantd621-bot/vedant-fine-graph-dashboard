"""
Enterprise Reporting REST Endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from backend.app.reporting.models import (
    CreateReportRequest, CreateScheduleRequest, ReportFormat, ReportSchedule,
    ReportSnapshot, ReportType
)
from backend.app.reporting.service import ReportingService, get_reporting_service
from backend.app.security.audit import get_audit_service
from backend.app.security.dependencies import require_admin, require_analyst
from backend.app.security.models import User

router = APIRouter(prefix="/api/v1/reports", tags=["reporting"])


@router.get("/types", response_model=List[str])
def list_report_types(current_user: User = Depends(require_analyst)):
    """List 8 supported enterprise report types."""
    return [t.value for t in ReportType]


@router.get("/schedules", response_model=List[ReportSchedule])
def list_schedules(
    current_user: User = Depends(require_analyst),
    service: ReportingService = Depends(get_reporting_service),
):
    """List active report schedules for the tenant."""
    return service.list_schedules(current_user.tenant_id)


@router.post("/schedules", response_model=ReportSchedule, status_code=status.HTTP_201_CREATED)
def create_schedule(
    req: CreateScheduleRequest,
    current_user: User = Depends(require_admin),
    service: ReportingService = Depends(get_reporting_service),
    audit = Depends(get_audit_service),
):
    """Create a recurring scheduled report."""
    schedule = service.create_schedule(req, current_user.tenant_id, current_user.username)
    audit.record(
        user_id=current_user.user_id,
        action="REPORT_SCHEDULE_CREATED",
        resource_type="REPORT_SCHEDULE",
        resource_id=schedule.schedule_id,
        tenant_id=current_user.tenant_id,
        new_value=schedule.title,
    )
    return schedule


@router.get("/", response_model=List[ReportSnapshot])
def list_snapshots(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_analyst),
    service: ReportingService = Depends(get_reporting_service),
):
    """List generated report snapshots."""
    return service.list_snapshots(current_user.tenant_id, limit=limit)


@router.post("/", response_model=ReportSnapshot, status_code=status.HTTP_201_CREATED)
def generate_report(
    req: CreateReportRequest,
    current_user: User = Depends(require_analyst),
    service: ReportingService = Depends(get_reporting_service),
    audit = Depends(get_audit_service),
):
    """Generate an immutable report snapshot with cryptographic SHA-256 hash."""
    snapshot = service.generate_report(req, current_user.tenant_id, current_user.username)
    audit.record(
        user_id=current_user.user_id,
        action="REPORT_GENERATED",
        resource_type="REPORT",
        resource_id=snapshot.report_id,
        tenant_id=current_user.tenant_id,
        new_value=snapshot.report_type.value,
    )
    return snapshot


@router.get("/{report_id}", response_model=ReportSnapshot)
def get_snapshot(
    report_id: str,
    current_user: User = Depends(require_analyst),
    service: ReportingService = Depends(get_reporting_service),
):
    """Retrieve an immutable report snapshot by ID."""
    snap = service.get_snapshot(report_id, current_user.tenant_id)
    if not snap:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return snap


@router.get("/{report_id}/export")
def export_snapshot(
    report_id: str,
    format: ReportFormat = Query(ReportFormat.JSON),
    current_user: User = Depends(require_analyst),
    service: ReportingService = Depends(get_reporting_service),
    audit = Depends(get_audit_service),
):
    """Export report snapshot as JSON or CSV with formula injection neutralization."""
    try:
        content, chash, media_type, filename = service.export_snapshot(report_id, current_user.tenant_id, format)
        audit.record(
            user_id=current_user.user_id,
            action="REPORT_EXPORTED",
            resource_type="REPORT",
            resource_id=report_id,
            tenant_id=current_user.tenant_id,
            new_value=format.value,
        )
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Content-Hash-SHA256": chash,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
