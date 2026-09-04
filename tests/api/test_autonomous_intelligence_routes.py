"""
Integration tests for Phase 17 Autonomous Intelligence, Shadow Detection,
Risk Calibration, and Threat Propagation REST Endpoints.
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


def test_summary_and_gap_routes(client, analyst_token, investigator_token):
    headers_ana = {"Authorization": f"Bearer {analyst_token}"}
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}

    # Summary
    sum_res = client.get("/api/v1/autonomous-intelligence/summary", headers=headers_ana)
    assert sum_res.status_code == 200
    data = sum_res.json()["data"]
    assert "active_gaps_count" in data
    assert "pending_recommendations_count" in data

    # Gaps list
    gaps_res = client.get("/api/v1/autonomous-intelligence/gaps", headers=headers_ana)
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()["data"]
    assert len(gaps) >= 1
    first_gap_id = gaps[0]["gap_id"]

    # Single gap
    gap_res = client.get(f"/api/v1/autonomous-intelligence/gaps/{first_gap_id}", headers=headers_ana)
    assert gap_res.status_code == 200
    assert gap_res.json()["data"]["gap_id"] == first_gap_id

    # 404 for nonexistent gap
    gap_404 = client.get("/api/v1/autonomous-intelligence/gaps/gap_missing_999", headers=headers_ana)
    assert gap_404.status_code == 404

    # Trigger scan
    scan_res = client.post("/api/v1/autonomous-intelligence/gaps/scan", headers=headers_inv)
    assert scan_res.status_code == 200
    assert len(scan_res.json()["data"]) >= 1


def test_recommendation_and_review_routes_rbac(client, analyst_token, investigator_token, admin_token):
    headers_ana = {"Authorization": f"Bearer {analyst_token}"}
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}
    headers_adm = {"Authorization": f"Bearer {admin_token}"}

    # List recommendations
    recs_res = client.get("/api/v1/autonomous-intelligence/recommendations", headers=headers_ana)
    assert recs_res.status_code == 200
    recs = recs_res.json()["data"]
    assert len(recs) >= 1
    target_rec_id = recs[0]["recommendation_id"]

    # Analyst cannot review (403 Forbidden)
    res_ana_review = client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{target_rec_id}/review",
        json={"status": "UNDER_REVIEW", "notes": "analyst attempt"},
        headers=headers_ana,
    )
    assert res_ana_review.status_code == 403

    # Investigator can review to UNDER_REVIEW
    res_inv_review = client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{target_rec_id}/review",
        json={"status": "UNDER_REVIEW", "notes": "investigator review"},
        headers=headers_inv,
    )
    assert res_inv_review.status_code == 200
    assert res_inv_review.json()["data"]["status"] == "UNDER_REVIEW"

    # Investigator cannot approve (403 Forbidden, admin required)
    res_inv_approve = client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{target_rec_id}/review",
        json={"status": "APPROVED", "notes": "investigator approve attempt"},
        headers=headers_inv,
    )
    assert res_inv_approve.status_code == 403

    # Admin can approve
    res_adm_approve = client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{target_rec_id}/review",
        json={"status": "APPROVED", "notes": "admin approval"},
        headers=headers_adm,
    )
    assert res_adm_approve.status_code == 200
    assert res_adm_approve.json()["data"]["status"] == "APPROVED"

    # Admin can deploy
    res_adm_deploy = client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{target_rec_id}/review",
        json={"status": "DEPLOYED", "notes": "admin deployment"},
        headers=headers_adm,
    )
    assert res_adm_deploy.status_code == 200
    assert res_adm_deploy.json()["data"]["status"] == "DEPLOYED"

    # Detector versions list
    vers_res = client.get("/api/v1/autonomous-intelligence/detector-versions", headers=headers_ana)
    assert vers_res.status_code == 200
    assert len(vers_res.json()["data"]) >= 1


def test_shadow_simulation_routes(client, analyst_token, investigator_token):
    headers_ana = {"Authorization": f"Bearer {analyst_token}"}
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}

    # Run simulation as investigator
    sim_payload = {
        "detector_id": "det_cycle_smurfing",
        "parameters": {"max_cycle_hops": 4, "min_amount_threshold": 9500.0},
        "time_window_hours": 24,
    }
    sim_res = client.post("/api/v1/autonomous-intelligence/shadow/simulate", json=sim_payload, headers=headers_inv)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()["data"]
    assert "simulation_id" in sim_data
    assert sim_data["alerts_would_fire_count"] > 0

    # List simulations as analyst
    list_res = client.get("/api/v1/autonomous-intelligence/shadow/simulations", headers=headers_ana)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # Single simulation
    sim_id = sim_data["simulation_id"]
    get_res = client.get(f"/api/v1/autonomous-intelligence/shadow/simulations/{sim_id}", headers=headers_ana)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["simulation_id"] == sim_id


def test_risk_calibration_routes(client, analyst_token, investigator_token):
    headers_ana = {"Authorization": f"Bearer {analyst_token}"}
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}

    # Get calibration
    res = client.get("/api/v1/autonomous-intelligence/risk-calibration?window_days=30", headers=headers_ana)
    assert res.status_code == 200
    cal_data = res.json()["data"]
    assert len(cal_data["buckets"]) == 5
    assert "overall_confirmation_rate" in cal_data

    # Refresh calibration
    ref_res = client.post("/api/v1/autonomous-intelligence/risk-calibration/refresh?window_days=60", headers=headers_inv)
    assert ref_res.status_code == 200
    assert ref_res.json()["data"]["evaluation_window_days"] == 60


def test_threat_propagation_routes(client, analyst_token, investigator_token):
    headers_ana = {"Authorization": f"Bearer {analyst_token}"}
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}

    # Analyze propagation
    prop_payload = {
        "origin_entity_id": "acc_target_123",
        "max_hops": 3,
        "time_window_hours": 24,
    }
    prop_res = client.post("/api/v1/autonomous-intelligence/threat-propagation/analyze", json=prop_payload, headers=headers_inv)
    assert prop_res.status_code == 200
    prop_data = prop_res.json()["data"]
    assert prop_data["origin_entity_id"] == "acc_target_123"
    assert "propagation_score" in prop_data
    assert len(prop_data["steps"]) == 4

    # Entity endpoint
    ent_res = client.get("/api/v1/autonomous-intelligence/threat-propagation/entities/acc_target_123?max_hops=2", headers=headers_ana)
    assert ent_res.status_code == 200
    assert ent_res.json()["data"]["origin_entity_id"] == "acc_target_123"
