"""
Security Headers, Rate Limiting, Request Size Limits & State Machine Validation Tests.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_neo4j_client
from backend.app.main import app
from backend.app.middleware.rate_limiter import reset_rate_limiter
from backend.app.security.jwt import create_access_token


def test_security_headers_and_request_id():
    """Verify security hardening headers and correlation request ID are injected."""
    mock_neo4j = MagicMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        response = client.get("/health")
        assert response.status_code == 200

        # Correlation ID
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"].startswith("req_")

        # Security Headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in response.headers
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    finally:
        app.dependency_overrides.clear()


def test_request_body_size_limit():
    """Verify oversized requests (> 2MB) are rejected with 413 Payload Too Large."""
    reset_rate_limiter()
    mock_neo4j = MagicMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        token = create_access_token({"sub": "usr_admin", "username": "admin", "role": "ADMIN"})
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Length": "3000000",  # > 2MB limit
        }
        resp = client.post("/api/v1/auth/login", json={"a": "b"}, headers=headers)
        assert resp.status_code == 413
        assert resp.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"

    finally:
        app.dependency_overrides.clear()
