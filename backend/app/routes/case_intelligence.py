"""
FinGraph Case Intelligence, Fraud Campaign, and Investigation Collaboration Endpoints.
Provides REST APIs for cross-case correlation, bounded relationship graphs,
forensic evidence provenance, multi-investigator collaboration, auditable comments,
chronological activity streams, fraud campaigns, and executive command center KPIs.
"""
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from backend.app.case_intelligence.exceptions import (
    CampaignNotFoundError,
    CaseNotFoundError,
    CommentNotFoundError,
    InvalidCollaboratorRoleError,
    UnauthorizedCollaborationError,
)
from backend.app.case_intelligence.models import (
    AddCollaboratorRequest,
    AddCommentRequest,
    Campaign,
    CampaignRiskExplanation,
    CampaignStatus,
    CampaignUpdateRequest,
    CaseActivityEvent,
    CaseCollaborator,
    CaseComment,
    CaseCorrelationResponse,
    CaseEvidenceProvenanceResponse,
    CaseRelationshipGraph,
    CommandCenterSummary,
    EnterpriseFraudPosture,
    EvidenceProvenance,
    UpdateCommentRequest,
)
from backend.app.case_intelligence.service import (
    CaseIntelligenceService,
    get_case_intelligence_service,
)
from backend.app.dependencies import get_case_service
from backend.app.models.cases import InvestigationCaseSummary
from backend.app.models.common import ApiResponse
from backend.app.security.dependencies import (
    require_analyst,
    require_investigator,
)
from backend.app.security.models import Role, User
from backend.app.services.case_service import CaseService

logger = logging.getLogger("FinGraph.CaseIntelligenceRouter")

router = APIRouter(prefix="/api/v1/case-intelligence", tags=["Enterprise Case Intelligence & Collaboration"])


# ---------------------------------------------------------------------------
# Cross-Case Intelligence & Relationship Graph
# ---------------------------------------------------------------------------

@router.get(
    "/cases/{case_id}/related",
    response_model=ApiResponse[CaseCorrelationResponse],
    summary="Get cross-case correlation links for an investigation case",
)
def get_related_cases(
    case_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Discovers and scores deterministic correlation links matching shared entities and patterns."""
    try:
        data = service.get_related_cases(case_id)
        return ApiResponse(data=data)
    except CaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": str(exc)},
        )


@router.get(
    "/cases/{case_id}/graph",
    response_model=ApiResponse[CaseRelationshipGraph],
    summary="Get bounded relationship graph for interactive visualization",
)
def get_case_relationship_graph(
    case_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Constructs bounded D3 force graph uniting cases, accounts, alerts, and evidence."""
    try:
        data = service.get_case_relationship_graph(case_id)
        return ApiResponse(data=data)
    except CaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": str(exc)},
        )


@router.get(
    "/cases/{case_id}/evidence-provenance",
    response_model=ApiResponse[CaseEvidenceProvenanceResponse],
    summary="Get explicit evidence provenance links for a case",
)
def get_evidence_provenance(
    case_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Traces evidence provenance connections (SUPPORTS, CONTRADICTS, DERIVED_FROM)."""
    try:
        data = service.get_evidence_provenance(case_id)
        return ApiResponse(data=data)
    except CaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": str(exc)},
        )


# ---------------------------------------------------------------------------
# Collaboration & Activity Logging
# ---------------------------------------------------------------------------

@router.get(
    "/cases/{case_id}/activity",
    response_model=ApiResponse[List[CaseActivityEvent]],
    summary="Get immutable chronological activity feed for a case",
)
def get_case_activity_feed(
    case_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Retrieves chronological activity and audit history for the case."""
    data = service.get_case_activity_feed(case_id)
    return ApiResponse(data=data)


@router.get(
    "/cases/{case_id}/collaborators",
    response_model=ApiResponse[List[CaseCollaborator]],
    summary="List assigned collaborators on a case",
)
def list_collaborators(
    case_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Lists investigators and watchers assigned to this case."""
    data = service.list_collaborators(case_id)
    return ApiResponse(data=data)


@router.post(
    "/cases/{case_id}/collaborators",
    response_model=ApiResponse[CaseCollaborator],
    status_code=status.HTTP_201_CREATED,
    summary="Add or update a collaborator on a case",
)
def add_collaborator(
    case_id: str,
    req: AddCollaboratorRequest,
    request: Request,
    current_user: User = Depends(require_investigator),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Assigns an investigator role (OWNER, COLLABORATOR, WATCHER) to a user."""
    req_id = getattr(request.state, "request_id", None)
    try:
        collab = service.add_collaborator(
            case_id=case_id,
            req=req,
            actor_id=current_user.user_id,
            actor_name=current_user.username,
            request_id=req_id,
        )
        return ApiResponse(data=collab)
    except CaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": str(exc)},
        )


@router.delete(
    "/cases/{case_id}/collaborators/{user_id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Remove a collaborator from a case",
)
def remove_collaborator(
    case_id: str,
    user_id: str,
    request: Request,
    current_user: User = Depends(require_investigator),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Removes a collaborator assignment from a case."""
    req_id = getattr(request.state, "request_id", None)
    success = service.remove_collaborator(
        case_id=case_id,
        user_id=user_id,
        actor_id=current_user.user_id,
        actor_name=current_user.username,
        request_id=req_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COLLABORATOR_NOT_FOUND", "message": f"Collaborator {user_id} not assigned to case"},
        )
    return ApiResponse(data={"success": True, "case_id": case_id, "user_id": user_id})


@router.get(
    "/cases/{case_id}/comments",
    response_model=ApiResponse[List[CaseComment]],
    summary="List active comments on a case",
)
def list_comments(
    case_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Lists non-deleted comments on a case."""
    comments = service.list_comments(case_id)
    return ApiResponse(data=comments)


@router.post(
    "/cases/{case_id}/comments",
    response_model=ApiResponse[CaseComment],
    status_code=status.HTTP_201_CREATED,
    summary="Post a comment on a case",
)
def add_comment(
    case_id: str,
    req: AddCommentRequest,
    request: Request,
    current_user: User = Depends(require_investigator),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Adds a new investigator comment with immutable audit tracking."""
    req_id = getattr(request.state, "request_id", None)
    try:
        comment = service.add_comment(
            case_id=case_id,
            req=req,
            author_id=current_user.user_id,
            author_name=current_user.username,
            request_id=req_id,
        )
        return ApiResponse(data=comment)
    except CaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": str(exc)},
        )


@router.patch(
    "/cases/{case_id}/comments/{comment_id}",
    response_model=ApiResponse[CaseComment],
    summary="Edit an existing comment",
)
def update_comment(
    case_id: str,
    comment_id: str,
    req: UpdateCommentRequest,
    request: Request,
    current_user: User = Depends(require_investigator),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Edits a comment content while preserving modification metadata."""
    req_id = getattr(request.state, "request_id", None)
    try:
        comment = service.update_comment(
            case_id=case_id,
            comment_id=comment_id,
            req=req,
            actor_id=current_user.user_id,
            actor_name=current_user.username,
            request_id=req_id,
        )
        return ApiResponse(data=comment)
    except CommentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMENT_NOT_FOUND", "message": str(exc)},
        )


@router.delete(
    "/cases/{case_id}/comments/{comment_id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Soft-delete a comment",
)
def delete_comment(
    case_id: str,
    comment_id: str,
    request: Request,
    current_user: User = Depends(require_investigator),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Soft-deletes a comment and logs an audit deletion entry."""
    req_id = getattr(request.state, "request_id", None)
    try:
        service.delete_comment(
            case_id=case_id,
            comment_id=comment_id,
            actor_id=current_user.user_id,
            actor_name=current_user.username,
            request_id=req_id,
        )
        return ApiResponse(data={"success": True, "comment_id": comment_id})
    except CommentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMENT_NOT_FOUND", "message": str(exc)},
        )


# ---------------------------------------------------------------------------
# Fraud Campaigns & Command Center
# ---------------------------------------------------------------------------

@router.get(
    "/campaigns",
    response_model=ApiResponse[List[Campaign]],
    summary="List multi-case fraud campaigns",
)
def list_campaigns(
    status_filter: Optional[CampaignStatus] = Query(None, alias="status"),
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Lists fraud campaigns matching optional status filter."""
    campaigns = service.list_campaigns(status=status_filter)
    return ApiResponse(data=campaigns)


@router.get(
    "/campaigns/{campaign_id}",
    response_model=ApiResponse[Campaign],
    summary="Get single campaign details",
)
def get_campaign(
    campaign_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Retrieves full campaign information and exposure statistics."""
    try:
        campaign = service.get_campaign(campaign_id)
        return ApiResponse(data=campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": str(exc)},
        )


@router.patch(
    "/campaigns/{campaign_id}",
    response_model=ApiResponse[Campaign],
    summary="Update campaign status or metadata",
)
def update_campaign(
    campaign_id: str,
    req: CampaignUpdateRequest,
    current_user: User = Depends(require_investigator),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Modifies campaign lifecycle status (CONFIRMED, UNDER_REVIEW, CLOSED) or title."""
    try:
        campaign = service.update_campaign(campaign_id, req, actor_name=current_user.username)
        return ApiResponse(data=campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": str(exc)},
        )


@router.get(
    "/campaigns/{campaign_id}/cases",
    response_model=ApiResponse[List[InvestigationCaseSummary]],
    summary="List investigation cases linked to a campaign",
)
def list_campaign_cases(
    campaign_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
    case_service: CaseService = Depends(get_case_service),
):
    """Retrieves summaries for all cases clustered under a campaign."""
    try:
        campaign = service.get_campaign(campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": str(exc)},
        )

    cases: List[InvestigationCaseSummary] = []
    for cid in campaign.case_ids:
        c = case_service.get_case_by_id(cid)
        if c:
            cases.append(
                InvestigationCaseSummary(
                    case_id=c.case_id,
                    title=c.title,
                    priority=c.priority,
                    status=c.status,
                    assigned_investigator=c.assigned_investigator,
                    alerts_count=len(c.linked_alerts),
                    accounts_count=len(c.linked_accounts),
                    notes_count=len(c.notes),
                    evidence_count=len(c.evidence),
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    created_by=c.created_by,
                )
            )
    return ApiResponse(data=cases)


@router.get(
    "/campaigns/{campaign_id}/graph",
    response_model=ApiResponse[CaseRelationshipGraph],
    summary="Get multi-case campaign relationship graph",
)
def get_campaign_graph(
    campaign_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Builds synthesized relationship graph for cases in the campaign."""
    try:
        campaign = service.get_campaign(campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": str(exc)},
        )

    focal_cid = campaign.case_ids[0] if campaign.case_ids else "CASE-2026-001"
    try:
        graph = service.get_case_relationship_graph(focal_cid)
        return ApiResponse(data=graph)
    except CaseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Primary case {focal_cid} not found"},
        )


@router.get(
    "/campaigns/{campaign_id}/evidence",
    response_model=ApiResponse[List[EvidenceProvenance]],
    summary="Get consolidated evidence provenance for a campaign",
)
def get_campaign_evidence(
    campaign_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Aggregates all provenance connections for cases in this campaign."""
    try:
        campaign = service.get_campaign(campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": str(exc)},
        )

    all_provenance: List[EvidenceProvenance] = []
    for cid in campaign.case_ids:
        try:
            prov = service.get_evidence_provenance(cid)
            all_provenance.extend(prov.records)
        except CaseNotFoundError:
            continue

    return ApiResponse(data=all_provenance)


@router.get(
    "/campaigns/{campaign_id}/explanation",
    response_model=ApiResponse[CampaignRiskExplanation],
    summary="Get 6-factor risk explanation for a campaign",
)
def get_campaign_explanation(
    campaign_id: str,
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Provides transparent, deterministic 6-factor risk score calculation."""
    try:
        exp = service.get_campaign_explanation(campaign_id)
        return ApiResponse(data=exp)
    except CampaignNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": str(exc)},
        )


# ---------------------------------------------------------------------------
# Executive Fraud Command Center
# ---------------------------------------------------------------------------

@router.get(
    "/command-center/summary",
    response_model=ApiResponse[CommandCenterSummary],
    summary="Get Executive Fraud Command Center operational KPIs",
)
def get_command_center_summary(
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Returns top-level enterprise KPIs, active campaigns, and posture score."""
    summary = service.get_command_center_summary()
    return ApiResponse(data=summary)


@router.get(
    "/command-center/posture",
    response_model=ApiResponse[EnterpriseFraudPosture],
    summary="Get explainable 0-100 Enterprise Fraud Posture evaluation",
)
def get_fraud_posture(
    current_user: User = Depends(require_analyst),
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
):
    """Evaluates enterprise fraud defense posture with positive/negative driver attribution."""
    posture = service.evaluate_fraud_posture()
    return ApiResponse(data=posture)
