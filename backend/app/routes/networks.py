"""
FinGraph Fraud Networks and Collusive Syndicates API Endpoints.
Exposes network discovery, topological scoring, member roles,
subgraphs, explainable risk breakdown, forensic evidence, and 1-click case promotion.
Protected by Authentication and RBAC.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from analytics.src.models import RiskLevel
from backend.app.dependencies import (
    get_graph_service,
    get_network_intelligence_service,
)
from backend.app.models.cases import InvestigationCase
from backend.app.models.graph import GraphPayload
from backend.app.models.networks import (
    FraudNetwork,
    NetworkCreateCaseRequest,
    NetworkDetail,
    NetworkEvidenceResponse,
    NetworkListResponse,
    NetworkMemberResponse,
    NetworkRiskExplanationResponse,
    NetworkSummary,
    NetworkType,
)
from backend.app.models.common import PaginationMeta
from backend.app.security.dependencies import require_analyst, require_investigator
from backend.app.security.models import User
from backend.app.services.graph_service import GraphService
from backend.app.services.network_intelligence_service import NetworkIntelligenceService

logger = logging.getLogger("FinGraph.NetworksRoute")

router = APIRouter(prefix="/api/v1/networks", tags=["Fraud Networks and Syndicates"])


@router.get("", response_model=NetworkListResponse)
def list_networks(
    network_type: Optional[NetworkType] = Query(None, description="Filter by network type"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum network risk score"),
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by risk severity"),
    min_members: Optional[int] = Query(None, ge=2, description="Minimum number of member accounts"),
    search: Optional[str] = Query(None, description="Search term for network name or member account ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(require_analyst),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
):
    """Retrieves paginated list of discovered fraud networks with multi-criteria filtering."""
    summaries, total_items = service.list_networks(
        network_type=network_type,
        min_risk_score=min_risk_score,
        risk_level=risk_level,
        min_members=min_members,
        search=search,
        page=page,
        page_size=page_size,
    )
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 1
    return NetworkListResponse(
        data=summaries,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.post("/discover", response_model=List[NetworkSummary])
def trigger_network_discovery(
    force_refresh: bool = Query(True, description="Force re-execution of discovery algorithms"),
    current_user: User = Depends(require_analyst),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
):
    """Executes network discovery algorithms (Cypher rings, Louvain communities, Hubs) and returns summaries."""
    networks = service.discover_networks(force_refresh=force_refresh)
    return [n.to_summary() for n in networks]


@router.get("/{network_id}", response_model=NetworkDetail)
def get_network_detail(
    network_id: str,
    current_user: User = Depends(require_analyst),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
):
    """Retrieves comprehensive details of a specific fraud network."""
    detail = service.get_network_by_id(network_id=network_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NETWORK_NOT_FOUND", "message": f"Fraud network '{network_id}' not found."},
        )
    return detail


@router.get("/{network_id}/members", response_model=NetworkMemberResponse)
def get_network_members(
    network_id: str,
    current_user: User = Depends(require_analyst),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
):
    """Retrieves structured list of member accounts in the network with inferred roles and graph metrics."""
    members_resp = service.get_network_members(network_id=network_id)
    if not members_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NETWORK_NOT_FOUND", "message": f"Fraud network '{network_id}' not found."},
        )
    return members_resp


@router.get("/{network_id}/subgraph", response_model=GraphPayload)
def get_network_subgraph(
    network_id: str,
    current_user: User = Depends(require_analyst),
    network_service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
    graph_service: GraphService = Depends(get_graph_service),
):
    """Retrieves interactive D3 graph payload representing all member accounts and interconnecting transfers."""
    network = network_service.get_network_by_id(network_id=network_id)
    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NETWORK_NOT_FOUND", "message": f"Fraud network '{network_id}' not found."},
        )
    member_ids = [m.account_id for m in network.members]
    return graph_service.get_network_subgraph(member_account_ids=member_ids)


@router.get("/{network_id}/risk-explanation", response_model=NetworkRiskExplanationResponse)
def get_network_risk_explanation(
    network_id: str,
    current_user: User = Depends(require_analyst),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
):
    """Retrieves deterministic mathematical breakdown of network risk factors and weights."""
    explanation = service.get_network_risk_explanation(network_id=network_id)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NETWORK_NOT_FOUND", "message": f"Fraud network '{network_id}' not found."},
        )
    return explanation


@router.get("/{network_id}/evidence", response_model=NetworkEvidenceResponse)
def get_network_evidence(
    network_id: str,
    current_user: User = Depends(require_analyst),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
):
    """Retrieves chronological timeline and forensic evidence items supporting network fraud classification."""
    evidence_resp = service.get_network_evidence(network_id=network_id)
    if not evidence_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NETWORK_NOT_FOUND", "message": f"Fraud network '{network_id}' not found."},
        )
    return evidence_resp


@router.post("/{network_id}/create-case", response_model=InvestigationCase, status_code=status.HTTP_201_CREATED)
def promote_network_to_case(
    network_id: str,
    request: NetworkCreateCaseRequest,
    current_user: User = Depends(require_investigator),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
):
    """
    Promotes a fraud network to a formal investigation case.
    RBAC: Requires INVESTIGATOR or ADMIN role.
    """
    case = service.promote_network_to_case(
        network_id=network_id,
        req=request,
        current_user=current_user,
    )
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NETWORK_NOT_FOUND", "message": f"Fraud network '{network_id}' not found."},
        )
    return case
