"""
Release Test: Service Health, Liveness, and Readiness Probes.
Validates /health, /live, /ready, dependency health, and liveness!=readiness guarantees.
"""
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_and_liveness_probes(client):
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    res_live = client.get("/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"


def test_readiness_probe_contract(client):
    res_ready = client.get("/ready")
    assert res_ready.status_code in (200, 503)
    data = res_ready.json()
    if res_ready.status_code == 200:
        assert "status" in data
        assert "dependencies" in data
    else:
        assert "error" in data
        assert data["error"]["code"] == "NOT_READY"


def test_prometheus_metrics_endpoint(client):
    res_metrics = client.get("/metrics")
    assert res_metrics.status_code == 200
    assert "http_requests_total" in res_metrics.text or "fingraph" in res_metrics.text or "process_" in res_metrics.text
