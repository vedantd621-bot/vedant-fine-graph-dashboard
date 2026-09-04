"""
Unit and integration tests for Password Hashing, JWT Tokens, and Authentication endpoints.
"""
from datetime import timedelta
import time
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_neo4j_client
from backend.app.main import app
from backend.app.security.jwt import create_access_token, decode_access_token
from backend.app.security.models import CreateUserRequest, Role
from backend.app.security.passwords import hash_password, verify_password
from backend.app.security.user_store import get_user_store


def test_password_hashing_and_verification():
    """Verify PBKDF2 cryptographic hashing and constant-time verification."""
    raw_pwd = "SuperSecretPassword123!"
    hashed = hash_password(raw_pwd)
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_generation_and_expiration():
    """Verify RFC 7519 JWT creation, claims decoding, and expiration."""
    claims = {"sub": "usr_test_123", "username": "testuser", "role": "ANALYST"}
    token = create_access_token(claims, expires_delta=timedelta(seconds=2))
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "usr_test_123"
    assert decoded["username"] == "testuser"

    # Test expired token
    expired_token = create_access_token(claims, expires_delta=timedelta(seconds=-10))
    assert decode_access_token(expired_token) is None


def test_login_success_and_current_user():
    """Verify successful login returns bearer token and /me profile retrieval."""
    mock_neo4j = MagicMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        # 1. Login with seeded admin account
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin_secret_pass_2026"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "ADMIN"

        token = data["access_token"]

        # 2. Access /me with bearer token
        me_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["username"] == "admin"
        assert me_data["role"] == "ADMIN"

    finally:
        app.dependency_overrides.clear()


def test_login_invalid_credentials():
    """Verify failed login returns 401 Unauthorized."""
    mock_neo4j = MagicMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "WrongPassword123!"},
        )
        assert resp.status_code == 401
        err_data = resp.json()
        assert err_data["error"]["code"] == "INVALID_CREDENTIALS"
    finally:
        app.dependency_overrides.clear()
