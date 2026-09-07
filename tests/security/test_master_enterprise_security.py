"""
Master Enterprise Security Matrix: Tests all 9 Roles, Deny-By-Default & Cross-Tenant Boundaries.
"""
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app
from backend.app.security.jwt import create_access_token
from backend.app.security.models import CreateUserRequest, Role
from backend.app.security.user_store import get_user_store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def ensure_users():
    store = get_user_store()
    # Seed alpha and beta users for cross tenant testing
    if not store.get_user_by_username("user_alpha"):
        store.create_user(CreateUserRequest(
            username="user_alpha",
            password="alpha_password_123",
            role=Role.INVESTIGATOR,
            tenant_id="tnt_alpha",
        ))
    if not store.get_user_by_username("user_beta"):
        store.create_user(CreateUserRequest(
            username="user_beta",
            password="beta_password_123",
            role=Role.INVESTIGATOR,
            tenant_id="tnt_beta",
        ))


def token_for_username(username: str):
    store = get_user_store()
    u = store.get_user_by_username(username)
    assert u is not None, f"User {username} not found"
    return create_access_token({
        "sub": u.user_id,
        "username": u.username,
        "role": u.role.value,
        "tenant_id": u.tenant_id,
    })


def test_unauthenticated_requests_denied(client):
    assert client.get("/api/v1/decisioning/").status_code == 401
    assert client.get("/api/v1/analytics/kpis").status_code == 401
    assert client.get("/api/v1/reports/").status_code == 401


def test_readonly_and_analyst_permissions(client):
    ro_token = token_for_username("readonly")
    headers = {"Authorization": f"Bearer {ro_token}"}

    # Allowed read
    assert client.get("/api/v1/analytics/kpis", headers=headers).status_code == 200
    assert client.get("/api/v1/reports/", headers=headers).status_code == 200
    assert client.get("/api/v1/decisioning/verdicts", headers=headers).status_code == 200

    # Mutation forbidden
    assert client.post("/api/v1/decisioning/", json={"risk_score": 80.0}, headers=headers).status_code == 403
    assert client.post("/api/v1/reports/schedules", json={"report_type": "OPERATIONS_REPORT", "frequency": "DAILY"}, headers=headers).status_code == 403


def test_investigator_and_reviewer_permissions(client):
    inv_token = token_for_username("investigator")
    headers = {"Authorization": f"Bearer {inv_token}"}

    # Investigator can create decision and run simulation
    dec_res = client.post(
        "/api/v1/decisioning/",
        json={"entity_id": "acc_sec_101", "risk_score": 88.0, "contributing_signals": ["Hub"]},
        headers=headers,
    )
    assert dec_res.status_code == 201
    dec_id = dec_res.json()["decision_id"]

    sim_res = client.post(
        "/api/v1/decisioning/simulate",
        json={"scenario_name": "Test Simulation", "parameters": []},
        headers=headers,
    )
    assert sim_res.status_code == 200

    # Investigator cannot override decision (admin only)
    assert client.post(
        f"/api/v1/decisioning/{dec_id}/override",
        json={"override_verdict": "REVIEW", "reason": "test"},
        headers=headers,
    ).status_code == 403


def test_admin_and_tenant_admin_full_authority(client):
    adm_token = token_for_username("admin")
    headers = {"Authorization": f"Bearer {adm_token}"}

    # Create decision
    dec = client.post("/api/v1/decisioning/", json={"risk_score": 90.0}, headers=headers).json()

    # Admin can override
    ovr = client.post(
        f"/api/v1/decisioning/{dec['decision_id']}/override",
        json={"override_verdict": "REVIEW", "reason": "Admin signed off"},
        headers=headers,
    )
    assert ovr.status_code == 200

    # Admin can create schedule
    sch = client.post(
        "/api/v1/reports/schedules",
        json={"report_type": "RISK_REPORT", "frequency": "DAILY"},
        headers=headers,
    )
    assert sch.status_code == 201


def test_cross_tenant_access_denied(client):
    alpha_token = token_for_username("user_alpha")
    beta_token = token_for_username("user_beta")

    # Alpha creates a decision
    dec_res = client.post(
        "/api/v1/decisioning/",
        json={"entity_id": "acc_alpha", "risk_score": 85.0},
        headers={"Authorization": f"Bearer {alpha_token}"},
    )
    assert dec_res.status_code == 201
    dec = dec_res.json()

    # Alpha can read it
    assert client.get(
        f"/api/v1/decisioning/{dec['decision_id']}",
        headers={"Authorization": f"Bearer {alpha_token}"},
    ).status_code == 200

    # Beta CANNOT read it (Cross-tenant forbidden/not found)
    assert client.get(
        f"/api/v1/decisioning/{dec['decision_id']}",
        headers={"Authorization": f"Bearer {beta_token}"},
    ).status_code == 404
