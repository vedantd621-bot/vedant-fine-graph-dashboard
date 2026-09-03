"""
FinGraph Interactive Graph Visualization Endpoints.
"""
from fastapi import APIRouter, Depends, Query

from backend.app.dependencies import get_neo4j_client, get_risk_engine
from backend.app.models.common import ApiResponse
from backend.app.models.graph import GraphPayload
from backend.app.services.graph_service import GraphService

router = APIRouter(prefix="/api/v1/accounts", tags=["Graph"])


def get_graph_service(
    client=Depends(get_neo4j_client),
    risk_eng=Depends(get_risk_engine),
) -> GraphService:
    return GraphService(client=client, risk_engine=risk_eng)


@router.get("/{account_id}/graph", response_model=ApiResponse[GraphPayload])
def get_account_subgraph(
    account_id: str,
    depth: int = Query(2, ge=1, le=3, description="Graph traversal hop depth (1 to 3)"),
    max_nodes: int = Query(100, ge=10, le=200),
    max_edges: int = Query(250, ge=20, le=500),
    service: GraphService = Depends(get_graph_service),
):
    """Retrieves bounded neighborhood subgraph centered on focal account for D3/React visualization."""
    payload = service.get_account_subgraph(
        account_id=account_id,
        depth=depth,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    return ApiResponse(data=payload)
