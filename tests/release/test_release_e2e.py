"""
Release Test: Cross-Subsystem E2E Integration.
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


def test_cross_subsystem_read_integration(client, analyst_token):
    hdrs = {"Authorization": f"Bearer {analyst_token}"}

    # Network Evolution
    res_evo = client.get("/api/v1/advanced-intelligence/networks/NET-001/evolution", headers=hdrs)
    assert res_evo.status_code == 200

    # Pattern Discovery
    res_pat = client.get("/api/v1/advanced-intelligence/patterns", headers=hdrs)
    assert res_pat.status_code == 200

    # Early Warnings
    res_warn = client.get("/api/v1/advanced-intelligence/early-warnings", headers=hdrs)
    assert res_warn.status_code == 200

    # Enterprise Threat Assessment
    res_threat = client.get("/api/v1/advanced-intelligence/threat-level", headers=hdrs)
    assert res_threat.status_code == 200
    assert "threat_level" in res_threat.json()["data"]

    # Autonomous Intelligence Summary
    res_auto = client.get("/api/v1/autonomous-intelligence/summary", headers=hdrs)
    assert res_auto.status_code == 200
