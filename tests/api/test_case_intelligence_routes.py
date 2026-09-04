"""
Integration tests for Phase 15 Case Intelligence & Collaboration REST routes.
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


def test_case_related_and_graph_endpoints(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # 1. Related cases
    res = client.get("/api/v1/case-intelligence/cases/CASE-2026-001/related", headers=headers)
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["case_id"] == "CASE-2026-001"
    assert "correlations" in body

    # 2. Relationship graph
    graph_res = client.get("/api/v1/case-intelligence/cases/CASE-2026-001/graph", headers=headers)
    assert graph_res.status_code == 200
    graph_body = graph_res.json()["data"]
    assert graph_body["focal_case_id"] == "CASE-2026-001"
    assert "nodes" in graph_body
    assert "edges" in graph_body

    # 3. Evidence provenance
    prov_res = client.get("/api/v1/case-intelligence/cases/CASE-2026-001/evidence-provenance", headers=headers)
    assert prov_res.status_code == 200
    assert "records" in prov_res.json()["data"]


def test_collaboration_and_comment_routes(client, investigator_token, analyst_token):
    inv_headers = {"Authorization": f"Bearer {investigator_token}"}
    ana_headers = {"Authorization": f"Bearer {analyst_token}"}

    case_id = "CASE-2026-001"

    # 1. Add collaborator (Investigator)
    add_collab_res = client.post(
        f"/api/v1/case-intelligence/cases/{case_id}/collaborators",
        headers=inv_headers,
        json={"user_id": "usr_test_collab", "username": "collab_user", "role": "COLLABORATOR"},
    )
    assert add_collab_res.status_code == 201

    # 2. List collaborators (Analyst can read)
    list_collab_res = client.get(f"/api/v1/case-intelligence/cases/{case_id}/collaborators", headers=ana_headers)
    assert list_collab_res.status_code == 200
    assert any(c["username"] == "collab_user" for c in list_collab_res.json()["data"])

    # 3. Add comment
    add_cmt_res = client.post(
        f"/api/v1/case-intelligence/cases/{case_id}/comments",
        headers=inv_headers,
        json={"content": "Integration test note on case."},
    )
    assert add_cmt_res.status_code == 201
    comment_id = add_cmt_res.json()["data"]["comment_id"]

    # 4. Update comment
    edit_cmt_res = client.patch(
        f"/api/v1/case-intelligence/cases/{case_id}/comments/{comment_id}",
        headers=inv_headers,
        json={"content": "Updated integration test note on case."},
    )
    assert edit_cmt_res.status_code == 200
    assert edit_cmt_res.json()["data"]["is_edited"] is True

    # 5. Delete comment
    del_cmt_res = client.delete(
        f"/api/v1/case-intelligence/cases/{case_id}/comments/{comment_id}",
        headers=inv_headers,
    )
    assert del_cmt_res.status_code == 200

    # 6. Activity feed
    act_res = client.get(f"/api/v1/case-intelligence/cases/{case_id}/activity", headers=ana_headers)
    assert act_res.status_code == 200
    assert len(act_res.json()["data"]) >= 1


def test_campaign_and_command_center_routes(client, analyst_token, investigator_token):
    ana_headers = {"Authorization": f"Bearer {analyst_token}"}
    inv_headers = {"Authorization": f"Bearer {investigator_token}"}

    # 1. List campaigns
    camp_list = client.get("/api/v1/case-intelligence/campaigns", headers=ana_headers)
    assert camp_list.status_code == 200
    campaigns = camp_list.json()["data"]
    assert len(campaigns) >= 1
    cid = campaigns[0]["campaign_id"]

    # 2. Get campaign detail & explanation
    camp_detail = client.get(f"/api/v1/case-intelligence/campaigns/{cid}", headers=ana_headers)
    assert camp_detail.status_code == 200

    camp_exp = client.get(f"/api/v1/case-intelligence/campaigns/{cid}/explanation", headers=ana_headers)
    assert camp_exp.status_code == 200
    assert "factors" in camp_exp.json()["data"]

    # 3. Update campaign status
    update_res = client.patch(
        f"/api/v1/case-intelligence/campaigns/{cid}",
        headers=inv_headers,
        json={"status": "CONFIRMED"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["status"] == "CONFIRMED"

    # 4. Command center summary & posture
    summary_res = client.get("/api/v1/case-intelligence/command-center/summary", headers=ana_headers)
    assert summary_res.status_code == 200
    assert "posture" in summary_res.json()["data"]

    posture_res = client.get("/api/v1/case-intelligence/command-center/posture", headers=ana_headers)
    assert posture_res.status_code == 200
    assert "posture_score" in posture_res.json()["data"]
