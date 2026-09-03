"""
Unit tests for typed RealtimeEvent schemas and JSON serialization.
"""
from datetime import datetime, timezone
import pytest

from detection.src.models import AlertStatus, DetectionType, Severity
from analytics.src.models import RiskLevel
from backend.app.realtime.events import (
    AlertCreatedPayload,
    AlertUpdatedPayload,
    EventType,
    GraphUpdatedPayload,
    RealtimeEvent,
    RiskUpdatedPayload,
    TransactionCreatedPayload,
    create_realtime_event,
)


def test_alert_created_event_serialization():
    """Verify alert.created envelope serialization."""
    payload = AlertCreatedPayload(
        alert_id="ALT_FUN_001",
        detection_type=DetectionType.FUNNEL,
        severity=Severity.HIGH,
        confidence=0.95,
        primary_account="A005",
        risk_score=82.5,
        risk_level=RiskLevel.CRITICAL,
        description="Funnel smurfing pattern detected",
        total_amount=36000.0,
        currency="USD",
        related_accounts=["A001", "A002"],
    )
    event = create_realtime_event(EventType.ALERT_CREATED, payload)

    json_dict = event.to_json_dict()
    assert json_dict["event"] == "alert.created"
    assert json_dict["version"] == 1
    assert json_dict["event_id"].startswith("evt_")
    assert json_dict["data"]["alert_id"] == "ALT_FUN_001"
    assert json_dict["data"]["severity"] == "HIGH"
    assert json_dict["data"]["risk_level"] == "CRITICAL"


def test_alert_updated_event_serialization():
    """Verify alert.updated envelope serialization."""
    payload = AlertUpdatedPayload(
        alert_id="ALT_FUN_001",
        previous_status=AlertStatus.OPEN,
        status=AlertStatus.INVESTIGATING,
        notes="Under forensic review",
    )
    event = create_realtime_event(EventType.ALERT_UPDATED, payload)

    json_dict = event.to_json_dict()
    assert json_dict["event"] == "alert.updated"
    assert json_dict["data"]["status"] == "INVESTIGATING"
    assert json_dict["data"]["previous_status"] == "OPEN"


def test_risk_updated_event_serialization():
    """Verify risk.updated envelope serialization."""
    payload = RiskUpdatedPayload(
        account_id="A005",
        previous_score=50.0,
        score=78.4,
        previous_level=RiskLevel.HIGH,
        risk_level=RiskLevel.CRITICAL,
        model_version="rule-gds-v1",
        reasons=["PageRank centrality is in the top 5%."],
    )
    event = create_realtime_event(EventType.RISK_UPDATED, payload)

    json_dict = event.to_json_dict()
    assert json_dict["event"] == "risk.updated"
    assert json_dict["data"]["account_id"] == "A005"
    assert json_dict["data"]["score"] == 78.4
    assert len(json_dict["data"]["reasons"]) == 1


def test_transaction_created_event_serialization():
    """Verify transaction.created envelope serialization."""
    payload = TransactionCreatedPayload(
        transaction_id="TX_1001",
        source_account="A001",
        destination_account="A005",
        amount=9500.0,
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        scenario_id="SC_FUNNEL_01",
    )
    event = create_realtime_event(EventType.TRANSACTION_CREATED, payload)

    json_dict = event.to_json_dict()
    assert json_dict["event"] == "transaction.created"
    assert json_dict["data"]["transaction_id"] == "TX_1001"
    assert json_dict["data"]["amount"] == 9500.0


def test_graph_updated_event_serialization():
    """Verify graph.updated envelope serialization."""
    payload = GraphUpdatedPayload(
        account_id="A005",
        change_type="TRANSACTION_ADDED",
        related_account_id="A001",
    )
    event = create_realtime_event(EventType.GRAPH_UPDATED, payload)

    json_dict = event.to_json_dict()
    assert json_dict["event"] == "graph.updated"
    assert json_dict["data"]["account_id"] == "A005"
    assert json_dict["data"]["change_type"] == "TRANSACTION_ADDED"
