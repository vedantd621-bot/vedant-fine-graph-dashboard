"""
Unit tests for WebSocketConnectionManager connection limits, subscriptions, and broadcasting.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest

from backend.app.realtime.connection_manager import WebSocketConnectionManager
from backend.app.realtime.event_bus import EventBus
from backend.app.realtime.events import (
    AlertCreatedPayload,
    EventType,
    create_realtime_event,
)
from detection.src.models import DetectionType, Severity


@pytest.mark.anyio
async def test_connection_manager_connect_and_disconnect():
    """Verify connect, active connection count, and disconnect."""
    bus = EventBus()
    mgr = WebSocketConnectionManager(event_bus=bus, max_clients=5)

    mock_ws = AsyncMock()
    accepted = await mgr.connect(mock_ws)
    assert accepted is True
    assert mgr.active_connections_count == 1

    await mgr.disconnect(mock_ws)
    assert mgr.active_connections_count == 0


@pytest.mark.anyio
async def test_connection_manager_capacity_limit():
    """Verify manager rejects connections beyond max_clients."""
    bus = EventBus()
    mgr = WebSocketConnectionManager(event_bus=bus, max_clients=2)

    ws1 = AsyncMock()
    ws2 = AsyncMock()
    ws3 = AsyncMock()

    assert await mgr.connect(ws1) is True
    assert await mgr.connect(ws2) is True
    assert await mgr.connect(ws3) is False
    assert mgr.active_connections_count == 2
    ws3.close.assert_called_once()


@pytest.mark.anyio
async def test_connection_manager_broadcast():
    """Verify broadcast delivers JSON event string to active websockets."""
    bus = EventBus()
    mgr = WebSocketConnectionManager(event_bus=bus, max_clients=5)

    ws1 = AsyncMock()
    ws2 = AsyncMock()
    await mgr.connect(ws1)
    await mgr.connect(ws2)

    payload = AlertCreatedPayload(
        alert_id="ALT_001",
        detection_type=DetectionType.FUNNEL,
        severity=Severity.HIGH,
        confidence=0.9,
        primary_account="A005",
        description="Funnel alert",
    )
    event = create_realtime_event(EventType.ALERT_CREATED, payload)

    await mgr.broadcast(event)

    ws1.send_text.assert_called_once()
    ws2.send_text.assert_called_once()
