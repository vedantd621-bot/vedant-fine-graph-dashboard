"""
Integration tests for FastAPI WebSocket endpoints (/api/v1/ws and /ws).
"""
import json
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_neo4j_client
from backend.app.main import app


def test_websocket_v1_connection_and_ping_pong():
    """Verify WebSocket /api/v1/ws handshake, welcome pong, and ping action."""
    mock_neo4j = MagicMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        with client.websocket_connect("/api/v1/ws") as websocket:
            # 1. Receive welcome message
            welcome_data = websocket.receive_text()
            welcome_json = json.loads(welcome_data)
            assert welcome_json["event"] == "system.pong"
            assert welcome_json["data"]["connected"] is True

            # 2. Send ping action
            websocket.send_text(json.dumps({"action": "ping"}))
            pong_data = websocket.receive_text()
            pong_json = json.loads(pong_data)
            assert pong_json["event"] == "system.pong"
            assert pong_json["data"]["pong"] is True

            # 3. Send subscribe action
            websocket.send_text(json.dumps({"action": "subscribe", "channels": ["alerts", "risk"]}))
            sub_data = websocket.receive_text()
            sub_json = json.loads(sub_data)
            assert "subscribed_channels" in sub_json["data"]

            # 4. Send watch_account action
            websocket.send_text(json.dumps({"action": "watch_account", "account_id": "A005"}))
            watch_data = websocket.receive_text()
            watch_json = json.loads(watch_data)
            assert watch_json["data"]["watching_account"] == "A005"
    finally:
        app.dependency_overrides.clear()
