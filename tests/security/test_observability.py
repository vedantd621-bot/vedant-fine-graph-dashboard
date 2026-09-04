"""
Observability, Health Probes and Prometheus Metrics Tests.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_neo4j_client
from backend.app.main import app


def test_liveness_and_readiness_probes():
    """Verify Kubernetes / Container liveness and readiness endpoints."""
    mock_neo4j = MagicMock()
    mock_neo4j.verify_connectivity.return_value = True
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        # Liveness
        live_res = client.get("/live")
        assert live_res.status_code == 200
        assert live_res.json()["status"] == "alive"

        # Readiness Healthy
        ready_res = client.get("/ready")
        assert ready_res.status_code == 200
        assert ready_res.json()["status"] == "ready"

        # Readiness Unhealthy
        mock_neo4j.verify_connectivity.return_value = False
        unready_res = client.get("/ready")
        assert unready_res.status_code == 503

    finally:
        app.dependency_overrides.clear()


def test_prometheus_metrics_endpoint():
    """Verify /metrics returns standard Prometheus text format."""
    mock_neo4j = MagicMock()
    mock_neo4j.verify_connectivity.return_value = True
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        metrics_res = client.get("/metrics")
        assert metrics_res.status_code == 200
        assert "text/plain" in metrics_res.headers["content-type"]
        text = metrics_res.text

        assert "fingraph_http_requests_total" in text
        assert "fingraph_websocket_active_connections" in text
        assert "fingraph_alerts_created_total" in text
        assert "fingraph_risk_calculations_total" in text

    finally:
        app.dependency_overrides.clear()
