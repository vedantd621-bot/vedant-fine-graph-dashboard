"""
Release Test: API Response Contracts & Envelope Schema Uniformity.
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


def test_api_response_envelope_uniformity(client, analyst_token):
    hdrs = {"Authorization": f"Bearer {analyst_token}"}
    endpoints = [
        "/api/v1/autonomous-intelligence/summary",
        "/api/v1/autonomous-intelligence/gaps",
        "/api/v1/autonomous-intelligence/recommendations",
        "/api/v1/autonomous-intelligence/detector-versions",
        "/api/v1/autonomous-intelligence/risk-calibration",
        "/api/v1/advanced-intelligence/threat-level",
    ]

    for ep in endpoints:
        res = client.get(ep, headers=hdrs)
        assert res.status_code == 200, f"Failed on {ep}"
        body = res.json()
        assert "data" in body, f"Missing 'data' key in response envelope for {ep}"
