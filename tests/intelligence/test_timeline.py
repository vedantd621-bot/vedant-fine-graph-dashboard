"""
Investigation Timeline Assembly Unit Tests.
Verifies chronological ordering and event categorization across transactions, detections, alerts, and cases.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from backend.app.dependencies import get_intelligence_service
from backend.app.main import app
from backend.app.models.intelligence import (
    EntityType,
    InvestigationTimelineEvent,
    InvestigationTimelineResponse,
    TimelineEventType,
)
from backend.app.security.jwt import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


def test_investigation_timeline_endpoint(client):
    """Verify GET /api/v1/entities/{id}/timeline returns chronological forensic event feed."""
    now = datetime.now(timezone.utc)
    mock_intel_service = MagicMock()
    mock_intel_service.get_entity_timeline.return_value = InvestigationTimelineResponse(
        entity_id="A001",
        total_events=4,
        events=[
            InvestigationTimelineEvent(
                timestamp=now,
                event_type=TimelineEventType.TRANSACTION,
                actor=None,
                entity_id="A001",
                title="Transaction OUTGOING: $25,000.00 USD",
                description="Outgoing transfer to A002 (TX_001).",
                evidence_ref="TX_001",
            ),
            InvestigationTimelineEvent(
                timestamp=now,
                event_type=TimelineEventType.DETECTOR_MATCH,
                actor="Cypher Engine",
                entity_id="A001",
                title="Pattern Match: CIRCULAR_FLOW",
                description="Closed 4-node wash trading loop discovered.",
                evidence_ref="FP_CIRC_001",
            ),
            InvestigationTimelineEvent(
                timestamp=now,
                event_type=TimelineEventType.ALERT_CREATED,
                actor="Alert Dispatcher",
                entity_id="A001",
                title="Alert Created (CRITICAL): ALT-CIRC-01",
                description="Topological circular wash alert dispatched.",
                evidence_ref="ALT-CIRC-01",
            ),
            InvestigationTimelineEvent(
                timestamp=now,
                event_type=TimelineEventType.CASE_CREATED,
                actor="investigator",
                entity_id="A001",
                title="Linked Case Opened: CASE-2026-001",
                description="Syndicate case opened.",
                evidence_ref="CASE-2026-001",
            ),
        ],
    )

    app.dependency_overrides[get_intelligence_service] = lambda: mock_intel_service
    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        res = client.get("/api/v1/entities/A001/timeline", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["entity_id"] == "A001"
        assert data["total_events"] == 4
        assert len(data["events"]) == 4
        assert data["events"][0]["event_type"] == "TRANSACTION"
        assert data["events"][1]["event_type"] == "DETECTOR_MATCH"
        assert data["events"][2]["event_type"] == "ALERT_CREATED"
        assert data["events"][3]["event_type"] == "CASE_CREATED"
    finally:
        app.dependency_overrides.clear()
