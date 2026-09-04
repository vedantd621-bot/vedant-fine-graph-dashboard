"""
Integration tests for Phase 19 Intelligence Orchestration REST routes.
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
def analyst_token():
    return create_access_token(payload={"sub": "usr_ana_003", "username": "analyst", "role": Role.ANALYST.value})

@pytest.fixture
def investigator_token():
    return create_access_token(payload={"sub": "usr_inv_002", "username": "investigator", "role": Role.INVESTIGATOR.value})

@pytest.fixture
def admin_token():
    return create_access_token(payload={"sub": "usr_admin_001", "username": "admin", "role": Role.ADMIN.value})


def test_correlations_routes(client, analyst_token, investigator_token):
    headers_ana = {"Authorization": f"Bearer {analyst_token}"}
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}
    
    # GET correlation
    res = client.get("/api/v1/orchestration/correlations/ALT-CIRC-01", headers=headers_ana)
    assert res.status_code == 200
    assert res.json()["data"]["primary_alert_id"] == "ALT-CIRC-01"
    
    # POST execute correlation
    res_post = client.post("/api/v1/orchestration/correlations/correlate?alert_id=ALT-CIRC-01", headers=headers_inv)
    assert res_post.status_code == 200
    assert res_post.json()["data"]["primary_alert_id"] == "ALT-CIRC-01"


def test_priority_calculate_route(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}
    payload = {
        "risk_score": 90.0,
        "financial_exposure": 150000.0,
        "alert_severity": "CRITICAL",
        "sla_hours_remaining": 1.5,
        "threat_propagation_score": 88.0,
        "has_active_campaign": True,
    }
    res = client.post("/api/v1/orchestration/priority/calculate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["priority_score"] >= 80.0
    assert data["priority_band"] == "CRITICAL"
    assert len(data["factors"]) == 6


def test_evidence_route(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}
    res = client.get("/api/v1/orchestration/evidence/CASE-2026-001", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 5


def test_brief_routes(client, analyst_token, investigator_token):
    headers_ana = {"Authorization": f"Bearer {analyst_token}"}
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}
    
    # GET brief
    res = client.get("/api/v1/orchestration/brief/CASE-2026-001", headers=headers_ana)
    assert res.status_code == 200
    assert res.json()["data"]["case_or_alert_id"] == "CASE-2026-001"
    
    # POST generate brief
    res_post = client.post("/api/v1/orchestration/brief/generate", json={"case_or_alert_id": "CASE-2026-001", "force_refresh": True}, headers=headers_inv)
    assert res_post.status_code == 200
    assert res_post.json()["data"]["case_or_alert_id"] == "CASE-2026-001"


def test_templates_routes(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}
    # List
    res = client.get("/api/v1/orchestration/templates", headers=headers)
    assert res.status_code == 200
    templates = res.json()["data"]
    assert len(templates) >= 4
    
    # Get one
    tmpl_id = templates[0]["template_id"]
    res_one = client.get(f"/api/v1/orchestration/templates/{tmpl_id}", headers=headers)
    assert res_one.status_code == 200
    assert res_one.json()["data"]["template_id"] == tmpl_id
    
    # 404
    res_404 = client.get("/api/v1/orchestration/templates/tmpl_non_existent", headers=headers)
    assert res_404.status_code == 404


def test_workflow_state_routes(client, analyst_token, investigator_token):
    headers_ana = {"Authorization": f"Bearer {analyst_token}"}
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}
    
    # GET state
    res = client.get("/api/v1/orchestration/cases/CASE-2026-001/workflow-state", headers=headers_ana)
    assert res.status_code == 200
    assert res.json()["data"] == "INVESTIGATING"
    
    # POST valid transition: INVESTIGATING -> EVIDENCE_REVIEW
    trans_res = client.post("/api/v1/orchestration/cases/CASE-2026-001/workflow-state", json={"to_state": "EVIDENCE_REVIEW", "notes": "Gathering graph data"}, headers=headers_inv)
    assert trans_res.status_code == 200
    assert trans_res.json()["data"] == "EVIDENCE_REVIEW"
    
    # POST invalid transition: EVIDENCE_REVIEW -> CREATED
    invalid_res = client.post("/api/v1/orchestration/cases/CASE-2026-001/workflow-state", json={"to_state": "CREATED"}, headers=headers_inv)
    assert invalid_res.status_code == 400


def test_task_and_checklist_routes(client, analyst_token, investigator_token):
    headers_ana = {"Authorization": f"Bearer {analyst_token}"}
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}
    
    # List tasks
    res = client.get("/api/v1/orchestration/tasks", headers=headers_ana)
    assert res.status_code == 200
    tasks = res.json()["data"]
    assert len(tasks) >= 2
    
    # Create task
    task_payload = {
        "case_id": "CASE-2026-001",
        "title": "Verify Proxy Origin",
        "description": "Examine subnet 198.51.100.0/24",
        "priority": "HIGH",
        "assignee": "investigator",
    }
    create_res = client.post("/api/v1/orchestration/tasks", json=task_payload, headers=headers_inv)
    assert create_res.status_code == 200
    task_id = create_res.json()["data"]["task_id"]
    
    # Update task
    update_res = client.put(f"/api/v1/orchestration/tasks/{task_id}", json={"status": "IN_PROGRESS"}, headers=headers_inv)
    assert update_res.status_code == 200
    assert update_res.json()["data"]["status"] == "IN_PROGRESS"
    
    # Complete task
    comp_res = client.post(f"/api/v1/orchestration/tasks/{task_id}/complete", headers=headers_inv)
    assert comp_res.status_code == 200
    assert comp_res.json()["data"]["status"] == "COMPLETED"
    
    # Checklist GET
    chk_res = client.get("/api/v1/orchestration/cases/CASE-2026-001/checklist", headers=headers_ana)
    assert chk_res.status_code == 200
    items = chk_res.json()["data"]
    assert len(items) >= 5
    
    # Checklist POST
    add_chk_res = client.post("/api/v1/orchestration/cases/CASE-2026-001/checklist", json={"title": "Escalate to FinCEN", "order": 10}, headers=headers_inv)
    assert add_chk_res.status_code == 200
    item_id = add_chk_res.json()["data"]["item_id"]
    
    # Checklist PUT
    put_chk_res = client.put(f"/api/v1/orchestration/cases/CASE-2026-001/checklist/{item_id}", json={"is_completed": True}, headers=headers_inv)
    assert put_chk_res.status_code == 200
    assert put_chk_res.json()["data"]["is_completed"] is True


def test_timeline_related_recommendations_and_search(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}
    
    # Timeline
    tl_res = client.get("/api/v1/orchestration/timeline/CASE-2026-001", headers=headers)
    assert tl_res.status_code == 200
    assert len(tl_res.json()["data"]) >= 6
    
    # Related cases
    rel_res = client.get("/api/v1/orchestration/related-cases/CASE-2026-001", headers=headers)
    assert rel_res.status_code == 200
    assert len(rel_res.json()["data"]) >= 2
    
    # Recommendations
    rec_res = client.get("/api/v1/orchestration/recommendations/CASE-2026-001", headers=headers)
    assert rec_res.status_code == 200
    assert len(rec_res.json()["data"]) >= 3
    
    # Search
    s_res = client.get("/api/v1/orchestration/search?q=acc_881", headers=headers)
    assert s_res.status_code == 200
    assert "acc_881" in s_res.json()["data"]["matched_accounts"]
