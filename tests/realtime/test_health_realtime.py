"""
Unit tests for GET /health/realtime endpoint.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_neo4j_client
from backend.app.main import app


def test_realtime_health_endpoint():
    """Verify /health/realtime returns active connection and consumer telemetry."""
    mock_neo4j = MagicMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        response = client.get("/health/realtime")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["enabled"] is True
        assert "connected_clients" in data
        assert "metrics" in data
    finally:
        app.dependency_overrides.clear()
