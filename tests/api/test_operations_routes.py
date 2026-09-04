"""
REST API Integration Tests for Phase 13 Operations & Notification Routes.
"""
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app
from backend.app.security.jwt import create_access_token
from backend.app.security.models import Role


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def analyst_token():
    return create_access_token(payload={"sub": "usr_ana_003", "username": "analyst", "role": Role.ANALYST.value})


@pytest.fixture
def investigator_token():
    return create_access_token(payload={"sub": "usr_inv_002", "username": "investigator", "role": Role.INVESTIGATOR.value})


@pytest.fixture
def admin_token():
    return create_access_token(payload={"sub": "usr_admin_001", "username": "admin", "role": Role.ADMIN.value})


def test_list_operations_alerts_and_queue(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # 1. List prioritized alerts
    res = client.get("/api/v1/operations/alerts?page=1&page_size=10", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert "data" in body
    assert "data" in body["data"]
    assert "pagination" in body["data"]

    # 2. Get investigator queue
    q_res = client.get("/api/v1/operations/queue", headers=headers)
    assert q_res.status_code == 200


def test_operations_summary_and_analytics_endpoints(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # Summary
    res = client.get("/api/v1/operations/summary", headers=headers)
    assert res.status_code == 200
    assert "alerts_today" in res.json()["data"]

    # Workload
    res = client.get("/api/v1/operations/workload", headers=headers)
    assert res.status_code == 200
    assert "investigators" in res.json()["data"]

    # SLA
    res = client.get("/api/v1/operations/sla", headers=headers)
    assert res.status_code == 200
    assert "compliance_rate" in res.json()["data"]

    # Trends
    res = client.get("/api/v1/operations/trends?interval=hourly", headers=headers)
    assert res.status_code == 200
    assert "points" in res.json()["data"]

    # Detectors
    res = client.get("/api/v1/operations/detectors", headers=headers)
    assert res.status_code == 200
    assert "detectors" in res.json()["data"]

    # Unified Search
    res = client.get("/api/v1/operations/search?q=alice", headers=headers)
    assert res.status_code == 200
    assert "results" in res.json()["data"]


def test_triage_rbac_permissions(client, analyst_token, investigator_token):
    # Analyst cannot mutate triage state (403 Forbidden)
    res_analyst = client.post(
        "/api/v1/operations/alerts/ALT-NONEXISTENT/triage",
        json={"new_status": "INVESTIGATING", "notes": "analyst attempt"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res_analyst.status_code == 403

    # Investigator is authorized to call triage (returns 400 because alert not found)
    res_inv = client.post(
        "/api/v1/operations/alerts/ALT-NONEXISTENT/triage",
        json={"new_status": "INVESTIGATING", "notes": "investigator attempt"},
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_inv.status_code in {400, 404}


def test_notifications_endpoints(client, investigator_token):
    headers = {"Authorization": f"Bearer {investigator_token}"}

    # List notifications
    res = client.get("/api/v1/notifications", headers=headers)
    assert res.status_code == 200
    assert "notifications" in res.json()["data"]

    # Mark all read
    res_all = client.post("/api/v1/notifications/read-all", headers=headers)
    assert res_all.status_code == 200
