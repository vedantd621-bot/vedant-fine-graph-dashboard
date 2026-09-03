"""
Unit tests for API health and liveness endpoints.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_neo4j_client
from backend.app.main import app


def test_health_endpoint():
    """Verify /health returns 200 OK status."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "fingraph-api"


def test_neo4j_health_check_healthy():
    """Verify /health/neo4j returns 200 when database is reachable."""
    mock_neo4j = MagicMock()
    mock_neo4j.verify_connectivity.return_value = True

    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        response = client.get("/health/neo4j")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "neo4j"
    finally:
        app.dependency_overrides.clear()


def test_neo4j_health_check_unhealthy():
    """Verify /health/neo4j returns 503 when database is unreachable."""
    mock_neo4j = MagicMock()
    mock_neo4j.verify_connectivity.return_value = False

    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        response = client.get("/health/neo4j")
        assert response.status_code == 503
        data = response.json()
        assert "error" in data or "detail" in data
    finally:
        app.dependency_overrides.clear()
