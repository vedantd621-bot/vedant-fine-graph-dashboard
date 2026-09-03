"""
Unit tests for async EventBus publish-subscribe lifecycle and exception isolation.
"""
import asyncio
import pytest

from backend.app.realtime.event_bus import EventBus
from backend.app.realtime.events import (
    EventType,
    GraphUpdatedPayload,
    create_realtime_event,
)


@pytest.mark.anyio
async def test_event_bus_publish_subscribe():
    """Verify event is delivered to multiple registered subscribers."""
    bus = EventBus()
    received_a = []
    received_b = []

    async def handler_a(event):
        received_a.append(event)

    async def handler_b(event):
        received_b.append(event)

    bus.subscribe("sub_a", handler_a)
    bus.subscribe("sub_b", handler_b)

    payload = GraphUpdatedPayload(account_id="A005", change_type="TRANSACTION_ADDED")
    event = create_realtime_event(EventType.GRAPH_UPDATED, payload)

    await bus.publish(event)

    assert len(received_a) == 1
    assert len(received_b) == 1
    assert received_a[0].event_id == event.event_id
    assert received_b[0].event_id == event.event_id
    assert bus.metrics["events_published"] == 1


@pytest.mark.anyio
async def test_event_bus_unsubscribe():
    """Verify unsubscribed handlers no longer receive events."""
    bus = EventBus()
    received = []

    async def handler(event):
        received.append(event)

    bus.subscribe("sub_1", handler)
    event1 = create_realtime_event(EventType.SYSTEM_PING, {"ping": True})
    await bus.publish(event1)
    assert len(received) == 1

    bus.unsubscribe("sub_1")
    event2 = create_realtime_event(EventType.SYSTEM_PING, {"ping": True})
    await bus.publish(event2)
    assert len(received) == 1


@pytest.mark.anyio
async def test_event_bus_exception_isolation():
    """Verify exception in one subscriber does not prevent delivery to other subscribers."""
    bus = EventBus()
    successful = []

    async def failing_handler(event):
        raise ValueError("Simulated subscriber crash")

    async def working_handler(event):
        successful.append(event)

    bus.subscribe("failing_sub", failing_handler)
    bus.subscribe("working_sub", working_handler)

    event = create_realtime_event(EventType.SYSTEM_PING, {"ping": True})
    await bus.publish(event)

    assert len(successful) == 1
    assert bus.metrics["events_failed"] == 1
