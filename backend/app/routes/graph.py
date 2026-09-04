"""
FinGraph Interactive Graph API Endpoints.
Serves bounded local subgraphs with strict depth and size limits.
Protected by Authentication and RBAC.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_graph_service
from backend.app.models.graph import GraphPayload
from backend.app.security.dependencies import require_analyst
from backend.app.security.models import User
from backend.app.services.graph_service import GraphService

router = APIRouter(prefix="/api/v1/accounts", tags=["Graph Visualizer"])


@router.get("/{account_id}/graph", response_model=GraphPayload)
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
