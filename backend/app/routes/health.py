"""
FinGraph Health & Liveness Endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from neo4j.src.client import Neo4jClient
from backend.app.dependencies import get_neo4j_client

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Returns basic API liveness status."""
    return {"status": "ok", "service": "fingraph-api"}


@router.get("/health/neo4j")
def neo4j_health_check(client: Neo4jClient = Depends(get_neo4j_client)):
    """Verifies live graph database connectivity."""
    is_connected = client.verify_connectivity()
    if not is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database": "neo4j", "error": "Cannot establish Bolt connection"},
        )
    return {"status": "ok", "database": "neo4j", "message": "Connection healthy"}
