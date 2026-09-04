"""
Latency and throughput measurement test for FinGraph real-time WebSocket pipeline.
Measures event dispatch, broadcast, and client receipt times under controlled conditions.
"""
import asyncio
import json
import statistics
import time
from typing import List
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_neo4j_client
from backend.app.main import app
from backend.app.security.jwt import create_access_token
from backend.app.realtime.connection_manager import get_connection_manager
from backend.app.realtime.event_bus import get_event_bus
from backend.app.realtime.events import (
    AlertCreatedPayload,
    EventType,
    create_realtime_event,
)
from detection.src.models import DetectionType, Severity


def test_realtime_websocket_latency_benchmark():
    """
    Measures end-to-end latency:
    Event published on EventBus -> Dispatched to ConnectionManager -> Transmitted over WebSocket -> Decoded by Client.
    """
    mock_neo4j = MagicMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    event_count = 50
    latencies_ms: List[float] = []

    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
            # Consume welcome message
            _ = ws.receive_text()

            conn_mgr = get_connection_manager()
            bus = get_event_bus()

            for i in range(event_count):
                payload = AlertCreatedPayload(
                    alert_id=f"ALT_BENCH_{i:03d}",
                    detection_type=DetectionType.CIRCULAR_FLOW,
                    severity=Severity.HIGH,
                    confidence=0.92,
                    primary_account=f"ACC_{i}",
                    risk_score=85.0,
                    description=f"Benchmark circular flow alert #{i}",
                )
                event = create_realtime_event(EventType.ALERT_CREATED, payload)

                t_start = time.perf_counter()
                asyncio.run(bus.publish(event))
                received_raw = ws.receive_text()
                t_end = time.perf_counter()

                received_json = json.loads(received_raw)
                assert received_json["data"]["alert_id"] == f"ALT_BENCH_{i:03d}"

                elapsed_ms = (t_end - t_start) * 1000.0
                latencies_ms.append(elapsed_ms)

        # Compute statistics
        latencies_ms.sort()
        min_lat = min(latencies_ms)
        max_lat = max(latencies_ms)
        median_lat = statistics.median(latencies_ms)
        p95_idx = int(0.95 * len(latencies_ms))
        p95_lat = latencies_ms[p95_idx]

        print(f"\n[Real-Time Latency Benchmark (n={event_count})]")
        print(f"  Min:    {min_lat:.3f} ms")
        print(f"  Median: {median_lat:.3f} ms")
        print(f"  P95:    {p95_lat:.3f} ms")
        print(f"  Max:    {max_lat:.3f} ms")

        # Assert sub-50ms latency in test environment
        assert median_lat < 50.0
        assert p95_lat < 100.0

    finally:
        app.dependency_overrides.clear()
