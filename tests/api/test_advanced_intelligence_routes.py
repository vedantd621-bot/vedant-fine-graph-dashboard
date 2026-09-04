"""
Integration tests for Phase 16 Advanced Graph Intelligence REST Endpoints.
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


def test_network_evolution_and_forecast_routes(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # 1. Network Evolution
    res = client.get("/api/v1/advanced-intelligence/networks/NET-001/evolution?window=1h", headers=headers)
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["network_id"] == "NET-001"
    assert "growth_rate" in body
    assert "velocity" in body

    # 2. Network Trajectory
    traj_res = client.get("/api/v1/advanced-intelligence/networks/NET-001/trajectory", headers=headers)
    assert traj_res.status_code == 200
    assert "trajectory" in traj_res.json()["data"]

    # 3. Network Forecast
    fore_res = client.get("/api/v1/advanced-intelligence/networks/NET-001/forecast", headers=headers)
    assert fore_res.status_code == 200
    assert "horizons" in fore_res.json()["data"]

    # 4. Entity Trajectory
    ent_res = client.get("/api/v1/advanced-intelligence/entities/account/A001/trajectory", headers=headers)
    assert ent_res.status_code == 200
    assert ent_res.json()["data"]["entity_id"] == "A001"

    # 5. Emerging Networks
    emg_res = client.get("/api/v1/advanced-intelligence/emerging-networks", headers=headers)
    assert emg_res.status_code == 200
    assert len(emg_res.json()["data"]) >= 1


def test_early_warning_and_action_routes(client, analyst_token, investigator_token):
    ana_headers = {"Authorization": f"Bearer {analyst_token}"}
    inv_headers = {"Authorization": f"Bearer {investigator_token}"}

    # 1. List Warnings
    w_list = client.get("/api/v1/advanced-intelligence/early-warnings", headers=ana_headers)
    assert w_list.status_code == 200
    warnings = w_list.json()["data"]
    assert len(warnings) >= 1
    w_id = warnings[0]["warning_id"]

    # 2. Acknowledge Warning (Investigator)
    ack_res = client.post(
        f"/api/v1/advanced-intelligence/early-warnings/{w_id}/acknowledge",
        headers=inv_headers,
        json={"notes": "Investigator test acknowledge"},
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["data"]["status"] == "ACKNOWLEDGED"

    # 3. Escalate Warning
    esc_res = client.post(
        f"/api/v1/advanced-intelligence/early-warnings/{w_id}/escalate",
        headers=inv_headers,
        json={"notes": "Investigator test escalate"},
    )
    assert esc_res.status_code == 200
    assert esc_res.json()["data"]["status"] == "ESCALATED"


def test_pattern_and_threat_routes(client, analyst_token):
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # 1. Patterns
    p_res = client.get("/api/v1/advanced-intelligence/patterns", headers=headers)
    assert p_res.status_code == 200
    patterns = p_res.json()["data"]
    assert len(patterns) >= 1
    p_id = patterns[0]["pattern_id"]

    # 2. Pattern Similarity
    sim_res = client.get(f"/api/v1/advanced-intelligence/patterns/{p_id}/similar", headers=headers)
    assert sim_res.status_code == 200
    assert len(sim_res.json()["data"]) >= 1

    # 3. Threat Level
    threat_res = client.get("/api/v1/advanced-intelligence/threat-level", headers=headers)
    assert threat_res.status_code == 200
    assert "threat_level" in threat_res.json()["data"]

    # 4. Enterprise Forecast
    fore_res = client.get("/api/v1/advanced-intelligence/enterprise-forecast", headers=headers)
    assert fore_res.status_code == 200
    assert "forecast_24h" in fore_res.json()["data"]

    # 5. Advanced Summary
    sum_res = client.get("/api/v1/advanced-intelligence/command-center/advanced-summary", headers=headers)
    assert sum_res.status_code == 200
    assert "threat" in sum_res.json()["data"]
