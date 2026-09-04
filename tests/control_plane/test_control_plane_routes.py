"""
Integration tests for Control Plane REST routes in Phase 20.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.security.jwt import create_access_token
from backend.app.security.models import Role

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def platform_token():
    return create_access_token(payload={"sub": "usr_plat_000", "username": "platform_admin", "role": "PLATFORM_ADMIN"})

@pytest.fixture
def admin_token():
    return create_access_token(payload={"sub": "usr_admin_001", "username": "admin", "role": Role.ADMIN.value})

@pytest.fixture
def analyst_token():
    return create_access_token(payload={"sub": "usr_ana_003", "username": "analyst", "role": Role.ANALYST.value})


def test_overview_endpoint(client, analyst_token, platform_token):
    res_ana = client.get("/api/v1/control-plane/overview", headers={"Authorization": f"Bearer {analyst_token}"})
    assert res_ana.status_code == 200
    assert res_ana.json()["data"]["scope"] == "TENANT"

    res_plat = client.get("/api/v1/control-plane/overview", headers={"Authorization": f"Bearer {platform_token}"})
    assert res_plat.status_code == 200
    assert res_plat.json()["data"]["scope"] == "GLOBAL_PLATFORM"


def test_tenants_crud_routes(client, platform_token):
    headers = {"Authorization": f"Bearer {platform_token}"}
    # List
    list_res = client.get("/api/v1/control-plane/tenants", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # Create
    create_res = client.post("/api/v1/control-plane/tenants", json={"name": "API Test Bank", "slug": "api-test-bank"}, headers=headers)
    assert create_res.status_code == 200
    tenant_id = create_res.json()["data"]["tenant_id"]

    # Detail
    det_res = client.get(f"/api/v1/control-plane/tenants/{tenant_id}", headers=headers)
    assert det_res.status_code == 200
    assert det_res.json()["data"]["slug"] == "api-test-bank"

    # Status transition
    st_res = client.post(f"/api/v1/control-plane/tenants/{tenant_id}/status", json={"target_status": "SUSPENDED", "reason": "Testing"}, headers=headers)
    assert st_res.status_code == 200
    assert st_res.json()["data"]["status"] == "SUSPENDED"


def test_organization_and_teams_routes(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # List orgs
    org_res = client.get("/api/v1/control-plane/organizations", headers=headers)
    assert org_res.status_code == 200
    assert len(org_res.json()["data"]) >= 1

    # Create team
    team_res = client.post("/api/v1/control-plane/teams", json={"org_id": "org_default", "name": "API Fast Squad"}, headers=headers)
    assert team_res.status_code == 200
    team_id = team_res.json()["data"]["team_id"]

    # Add member
    add_res = client.post(f"/api/v1/control-plane/teams/{team_id}/members", json={"user_id": "usr_inv_99", "username": "bob", "role": "ANALYST"}, headers=headers)
    assert add_res.status_code == 200
    assert len(add_res.json()["data"]["members"]) >= 1


def test_users_and_roles_routes(client, admin_token, analyst_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # List users
    users_res = client.get("/api/v1/control-plane/users", headers=headers)
    assert users_res.status_code == 200
    assert len(users_res.json()["data"]) >= 3

    # Invite user
    inv_res = client.post("/api/v1/control-plane/users/invite", json={"username": "new_analyst_2026", "password": "pass_123", "role": "ANALYST"}, headers=headers)
    assert inv_res.status_code == 200
    new_uid = inv_res.json()["data"]["user_id"]

    # Update user status
    st_res = client.post(f"/api/v1/control-plane/users/{new_uid}/status", json={"target_status": "SUSPENDED"}, headers=headers)
    assert st_res.status_code == 200
    assert st_res.json()["data"]["is_active"] is False

    # Roles & Permissions
    roles_res = client.get("/api/v1/control-plane/roles", headers={"Authorization": f"Bearer {analyst_token}"})
    assert roles_res.status_code == 200
    perms_res = client.get("/api/v1/control-plane/permissions", headers={"Authorization": f"Bearer {analyst_token}"})
    assert perms_res.status_code == 200
    assert len(perms_res.json()["data"]) >= 10


def test_policies_routes(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # List policies
    list_res = client.get("/api/v1/control-plane/policies", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # Create policy
    create_res = client.post("/api/v1/control-plane/policies", json={"name": "Test Allow Route", "resource": "alerts", "action": "read", "effect": "ALLOW", "priority": 120}, headers=headers)
    assert create_res.status_code == 200
    pol_id = create_res.json()["data"]["policy_id"]

    # Evaluate dry-run
    eval_res = client.post("/api/v1/control-plane/policies/evaluate", json={
        "user_id": "usr_01",
        "role": "INVESTIGATOR",
        "tenant_id": "tnt_default",
        "resource_type": "case",
        "resource_id": "case_1",
        "resource_tenant_id": "tnt_default",
        "action": "read"
    }, headers=headers)
    assert eval_res.status_code == 200
    assert eval_res.json()["data"]["is_allowed"] is True


def test_tenant_audit_logs(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}
    res = client.get("/api/v1/control-plane/audit", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)
