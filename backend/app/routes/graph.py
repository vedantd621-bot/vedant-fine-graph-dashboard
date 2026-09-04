"""
FinGraph Interactive Graph API Endpoints.
Serves bounded local subgraphs, suspicious neighborhoods, and common counterparty intersections.
Protected by Authentication and RBAC.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_graph_service
from backend.app.models.graph import GraphPayload
from backend.app.security.dependencies import require_analyst
from backend.app.security.models import User
from backend.app.services.graph_service import GraphService

router = APIRouter(tags=["Graph Visualizer & Network Forensics"])


@router.get("/api/v1/accounts/{account_id}/graph", response_model=GraphPayload)
def get_account_subgraph(
    account_id: str,
    depth: int = Query(2, ge=1, le=3, description="Graph traversal hop depth (1 to 3)"),
    max_nodes: int = Query(100, ge=10, le=100, description="Upper bound on total nodes to render"),
    max_edges: int = Query(250, ge=10, le=250, description="Upper bound on total relationships to render"),
    current_user: User = Depends(require_analyst),
    service: GraphService = Depends(get_graph_service),
):
    """Retrieves bounded neighborhood graph for interactive D3 network visualization."""
    return service.get_account_subgraph(
        account_id=account_id,
        depth=depth,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )


@router.get("/api/v1/graph/neighborhood/{account_id}", response_model=GraphPayload)
def get_graph_neighborhood(
    account_id: str,
    hops: int = Query(2, ge=1, le=3, description="Traversal hop depth"),
    max_nodes: int = Query(100, ge=10, le=100, description="Maximum nodes"),
    current_user: User = Depends(require_analyst),
    service: GraphService = Depends(get_graph_service),
):
    """Retrieves bounded 1-2 hop neighborhood graph centered on an account."""
    return service.get_account_subgraph(
        account_id=account_id,
        depth=hops,
        max_nodes=max_nodes,
    )


@router.get("/api/v1/graph/suspicious-neighborhood/{account_id}", response_model=GraphPayload)
def get_suspicious_neighborhood(
    account_id: str,
    min_risk: float = Query(60.0, ge=0.0, le=100.0, description="Minimum risk score threshold for filtered subgraph"),
    max_hops: int = Query(2, ge=1, le=3, description="Traversal hop depth"),
    current_user: User = Depends(require_analyst),
    service: GraphService = Depends(get_graph_service),
):
    """Retrieves filtered subgraph showing only elevated-risk counterparties and connections."""
    return service.get_suspicious_neighborhood(
        account_id=account_id,
        min_risk=min_risk,
        max_hops=max_hops,
    )


@router.get("/api/v1/graph/common-counterparties")
def get_common_counterparties(
    account_a: str = Query(..., description="First account ID"),
    account_b: str = Query(..., description="Second account ID"),
    current_user: User = Depends(require_analyst),
    service: GraphService = Depends(get_graph_service),
):
    """Finds common direct or indirect transaction counterparties connecting two accounts."""
    if account_a == account_b:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "IDENTICAL_ACCOUNTS", "message": "account_a and account_b must be distinct."},
        )

    records = service.get_common_counterparties(account_a=account_a, account_b=account_b)
    return {
        "account_a": account_a,
        "account_b": account_b,
        "common_counterparties_count": len(records),
        "data": records,
    }
