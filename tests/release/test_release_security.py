"""
Release Test: Security, Headers, Token Expiration, and Injection Protections.
"""
from datetime import timedelta
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app
from backend.app.security.jwt import create_access_token
from backend.app.security.models import Role


@pytest.fixture
def client():
    return TestClient(app)


def test_security_headers_present(client):
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") in ("DENY", "SAMEORIGIN")
    assert "X-XSS-Protection" in res.headers or "Content-Security-Policy" in res.headers


def test_invalid_and_expired_tokens_rejected(client):
    # Missing token
    res_missing = client.get("/api/v1/autonomous-intelligence/summary")
    assert res_missing.status_code in (401, 403)

    # Malformed token
    res_malformed = client.get("/api/v1/autonomous-intelligence/summary", headers={"Authorization": "Bearer invalid_garbage_token"})
    assert res_malformed.status_code in (401, 403)

    # Expired token (iat & exp in past)
    expired_token = create_access_token(
        {"sub": "usr_ana_003", "username": "analyst", "role": Role.ANALYST.value},
        expires_delta=timedelta(hours=-1)
    )
    res_expired = client.get("/api/v1/autonomous-intelligence/summary", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code in (401, 403)


def test_injection_resilience_in_parameters(client):
    token = create_access_token({"sub": "usr_ana_003", "username": "analyst", "role": Role.ANALYST.value})
    headers = {"Authorization": f"Bearer {token}"}

    # Cypher / SQL injection attempt in URL parameters
    payloads = [
        "' OR 1=1 --",
        "MATCH (n) DETACH DELETE n",
        "<script>alert('xss')</script>",
        "../../../../etc/passwd",
    ]
    for p in payloads:
        res = client.get(f"/api/v1/autonomous-intelligence/gaps/{p}", headers=headers)
        assert res.status_code in (400, 404, 422)  # Safely rejected without 500 crashes
