"""
Release Test: Complete RBAC Authorization Matrix (ANALYST, INVESTIGATOR, ADMIN).
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
    return create_access_token({"sub": "usr_ana_003", "username": "analyst", "role": Role.ANALYST.value})


@pytest.fixture
def investigator_token():
    return create_access_token({"sub": "usr_inv_002", "username": "investigator", "role": Role.INVESTIGATOR.value})


@pytest.fixture
def admin_token():
    return create_access_token({"sub": "usr_admin_001", "username": "admin", "role": Role.ADMIN.value})


def test_rbac_authorization_matrix(client, analyst_token, investigator_token, admin_token):
    ana_hdrs = {"Authorization": f"Bearer {analyst_token}"}
    inv_hdrs = {"Authorization": f"Bearer {investigator_token}"}
    adm_hdrs = {"Authorization": f"Bearer {admin_token}"}

    # 1. ANALYST: Read allowed, mutation forbidden
    assert client.get("/api/v1/autonomous-intelligence/summary", headers=ana_hdrs).status_code == 200
    assert client.post("/api/v1/autonomous-intelligence/gaps/scan", headers=ana_hdrs).status_code == 403

    # 2. INVESTIGATOR: Read + Scan + Triage allowed, Approval/Deployment forbidden
    assert client.post("/api/v1/autonomous-intelligence/gaps/scan", headers=inv_hdrs).status_code == 200
    recs = client.get("/api/v1/autonomous-intelligence/recommendations", headers=inv_hdrs).json()["data"]
    rec_id = recs[0]["recommendation_id"]
    
    # Investigator cannot approve or deploy
    assert client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{rec_id}/review",
        json={"status": "APPROVED", "notes": "unauthorized attempt"},
        headers=inv_hdrs,
    ).status_code == 403

    # 3. ADMIN: Full authority
    assert client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{rec_id}/review",
        json={"status": "APPROVED", "notes": "admin approval"},
        headers=adm_hdrs,
    ).status_code == 200
