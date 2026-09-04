"""
WebSocket Authentication and Authorization Tests.
"""
import json
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app.dependencies import get_neo4j_client
from backend.app.main import app
from backend.app.security.jwt import create_access_token


def test_unauthenticated_websocket_rejected():
    """Verify unauthenticated WebSocket connection attempt is closed with 1008 Policy Violation."""
    mock_neo4j = MagicMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/api/v1/ws") as ws:
                _ = ws.receive_text()
        assert excinfo.value.code == 1008
    finally:
        app.dependency_overrides.clear()


def test_authenticated_websocket_connection_success():
    """Verify authenticated WebSocket connection with JWT token succeeds and receives welcome payload."""
    mock_neo4j = MagicMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        token = create_access_token({"sub": "usr_inv_002", "username": "investigator", "role": "INVESTIGATOR"})
        with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
            welcome_raw = ws.receive_text()
            welcome_data = json.loads(welcome_raw)
            assert welcome_data["event"] == "system.pong"
            assert welcome_data["data"]["connected"] is True
            assert welcome_data["data"]["authenticated_as"] == "investigator"
            assert welcome_data["data"]["role"] == "INVESTIGATOR"
    finally:
        app.dependency_overrides.clear()
