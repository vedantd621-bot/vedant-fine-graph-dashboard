"""
FinGraph Case Management API Endpoints.
Provides complete case lifecycle operations, notes, cryptographic evidence attachments,
alert/account linking, investigator assignments, and timeline extraction.
Protected by Authentication and RBAC.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_case_service
from backend.app.models.cases import (
    CaseAssignRequest,
    CaseCreateRequest,
    CaseLinkAccountRequest,
    CaseLinkAlertRequest,
    CaseListResponse,
    CaseNoteCreateRequest,
    CasePriority,
    CaseStatus,
    CaseUpdateRequest,
    EvidenceCreateRequest,
    EvidenceItem,
    InvestigationCase,
    InvestigationNote,
)
from backend.app.models.intelligence import InvestigationTimelineResponse
from backend.app.security.audit import AuditService, get_audit_service
from backend.app.security.dependencies import require_analyst, require_investigator
from backend.app.security.models import User
from backend.app.services.case_service import ALLOWED_CASE_TRANSITIONS, CaseService

router = APIRouter(prefix="/api/v1/cases", tags=["Investigation Case Management"])


@router.get("", response_model=CaseListResponse)
def list_cases(
    status_filter: Optional[CaseStatus] = Query(None, alias="status", description="Filter by case status"),
    priority: Optional[CasePriority] = Query(None, description="Filter by case priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned investigator username"),
    search: Optional[str] = Query(None, description="Free text search query across title, description, and accounts"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(require_analyst),
    service: CaseService = Depends(get_case_service),
):
    """Lists investigation cases with multi-attribute filtering and pagination."""
    items, total = service.list_cases(
        status=status_filter,
        priority=priority,
        assigned_to=assigned_to,
        search=search,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return CaseListResponse(
        data=items,
        total_items=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=InvestigationCase, status_code=status.HTTP_201_CREATED)
def create_case(
    req: CaseCreateRequest,
    current_user: User = Depends(require_investigator),
    service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Creates and opens a new investigation case (INVESTIGATOR or ADMIN only)."""
    case = service.create_case(
        req=req,
        author_id=current_user.user_id,
        author_name=current_user.username,
    )

    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="CASE_CREATE",
        resource_type="CASE",
        resource_id=case.case_id,
        old_value=None,
        new_value=case.status.value,
    )

    return case


@router.get("/{case_id}", response_model=InvestigationCase)
def get_case_detail(
    case_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseService = Depends(get_case_service),
):
    """Retrieves full case details including note thread, evidence items, and linked entities."""
    case = service.get_case_by_id(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )
    return case


@router.patch("/{case_id}", response_model=InvestigationCase)
def update_case(
    case_id: str,
    req: CaseUpdateRequest,
    current_user: User = Depends(require_investigator),
    service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Updates case status, priority, title, or description with state transition validation."""
    current_case = service.get_case_by_id(case_id)
    if not current_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )

    # Validate state transition if status change requested
    if req.status is not None and req.status != current_case.status:
        allowed = ALLOWED_CASE_TRANSITIONS.get(current_case.status, set())
        if req.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_CASE_TRANSITION",
                    "message": f"Cannot transition case status from '{current_case.status.value}' to '{req.status.value}'. Allowed: {[s.value for s in allowed]}",
                },
            )

    updated = service.update_case(case_id, req, actor_name=current_user.username)

    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="CASE_UPDATE",
        resource_type="CASE",
        resource_id=case_id,
        old_value=current_case.status.value,
        new_value=updated.status.value,
    )

    return updated


@router.post("/{case_id}/assign", response_model=InvestigationCase)
def assign_investigator(
    case_id: str,
    req: CaseAssignRequest,
    current_user: User = Depends(require_investigator),
    service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Assigns or transfers case ownership to an investigator."""
    current_case = service.get_case_by_id(case_id)
    if not current_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )

    updated = service.assign_investigator(
        case_id=case_id,
        investigator=req.assigned_investigator,
        actor_name=current_user.username,
    )

    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="CASE_ASSIGN",
        resource_type="CASE",
        resource_id=case_id,
        old_value=current_case.assigned_investigator,
        new_value=req.assigned_investigator,
    )

    return updated


@router.post("/{case_id}/notes", response_model=InvestigationNote, status_code=status.HTTP_201_CREATED)
def add_case_note(
    case_id: str,
    req: CaseNoteCreateRequest,
    current_user: User = Depends(require_investigator),
    service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Appends an investigator note to a case note feed."""
    note = service.add_note(
        case_id=case_id,
        content=req.content,
        author_id=current_user.user_id,
        author_name=current_user.username,
    )
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )

    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="CASE_NOTE_ADD",
        resource_type="CASE",
        resource_id=case_id,
        old_value=None,
        new_value=note.note_id,
    )

    return note


@router.post("/{case_id}/evidence", response_model=EvidenceItem, status_code=status.HTTP_201_CREATED)
def attach_evidence(
    case_id: str,
    req: EvidenceCreateRequest,
    current_user: User = Depends(require_investigator),
    service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Registers and cryptographically hashes a forensic evidence item attached to a case."""
    evidence = service.add_evidence(
        case_id=case_id,
        req=req,
        author_id=current_user.user_id,
        author_name=current_user.username,
    )
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )

    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="CASE_EVIDENCE_ATTACH",
        resource_type="CASE",
        resource_id=case_id,
        old_value=None,
        new_value=f"{evidence.evidence_id}:{evidence.integrity_hash[:8]}",
    )

    return evidence


@router.post("/{case_id}/alerts", response_model=InvestigationCase)
def link_alert_to_case(
    case_id: str,
    req: CaseLinkAlertRequest,
    current_user: User = Depends(require_investigator),
    service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Associates an alert ID with a case."""
    case = service.link_alert(case_id=case_id, alert_id=req.alert_id, actor_name=current_user.username)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )

    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="CASE_LINK_ALERT",
        resource_type="CASE",
        resource_id=case_id,
        old_value=None,
        new_value=req.alert_id,
    )

    return case


@router.delete("/{case_id}/alerts/{alert_id}", response_model=InvestigationCase)
def unlink_alert_from_case(
    case_id: str,
    alert_id: str,
    current_user: User = Depends(require_investigator),
    service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Unlinks an alert ID from a case."""
    case = service.unlink_alert(case_id=case_id, alert_id=alert_id, actor_name=current_user.username)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )

    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="CASE_UNLINK_ALERT",
        resource_type="CASE",
        resource_id=case_id,
        old_value=alert_id,
        new_value=None,
    )

    return case


@router.post("/{case_id}/accounts", response_model=InvestigationCase)
def link_account_to_case(
    case_id: str,
    req: CaseLinkAccountRequest,
    current_user: User = Depends(require_investigator),
    service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Associates an account ID with a case."""
    case = service.link_account(case_id=case_id, account_id=req.account_id, actor_name=current_user.username)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )

    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="CASE_LINK_ACCOUNT",
        resource_type="CASE",
        resource_id=case_id,
        old_value=None,
        new_value=req.account_id,
    )

    return case


@router.delete("/{case_id}/accounts/{account_id}", response_model=InvestigationCase)
def unlink_account_from_case(
    case_id: str,
    account_id: str,
    current_user: User = Depends(require_investigator),
    service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Unlinks an account ID from a case."""
    case = service.unlink_account(case_id=case_id, account_id=account_id, actor_name=current_user.username)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )

    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="CASE_UNLINK_ACCOUNT",
        resource_type="CASE",
        resource_id=case_id,
        old_value=account_id,
        new_value=None,
    )

    return case


@router.get("/{case_id}/timeline", response_model=InvestigationTimelineResponse)
def get_case_timeline(
    case_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseService = Depends(get_case_service),
):
    """Constructs the chronological forensic timeline of events for a case."""
    case = service.get_case_by_id(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found."},
        )

    events = service.get_case_timeline(case_id)
    return InvestigationTimelineResponse(
        entity_id=case_id,
        total_events=len(events),
        events=events,
    )
