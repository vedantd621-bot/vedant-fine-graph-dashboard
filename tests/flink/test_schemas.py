"""
Unit tests for FinGraph Flink Canonical Schemas and Models.
"""
from datetime import datetime, timezone
import json
import pytest

from flink.src.schemas import CanonicalTransaction, DLQEvent, ValidationResult


def test_canonical_transaction_to_neo4j_dict():
    """Verify CanonicalTransaction serializes correctly for Neo4j Cypher parameters."""
    dt = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    tx = CanonicalTransaction(
        transaction_id="TX_TEST_001",
        from_account="A001",
        to_account="A002",
        amount=1500.50,
        currency="USD",
        timestamp=dt,
        scenario_id="SC_NORMAL",
        transaction_type="salary",
        channel="wire",
        from_person_id="P001",
        to_person_id="P002",
        from_bank_id="B01",
        to_bank_id="B02",
        from_account_type="checking",
        to_account_type="savings",
    )

    neo4j_dict = tx.to_neo4j_dict()
    assert neo4j_dict["transaction_id"] == "TX_TEST_001"
    assert neo4j_dict["from_account"] == "A001"
    assert neo4j_dict["to_account"] == "A002"
    assert neo4j_dict["amount"] == 1500.50
    assert neo4j_dict["currency"] == "USD"
    assert neo4j_dict["timestamp"] == "2026-08-15T12:00:00+00:00"
    assert neo4j_dict["scenario_id"] == "SC_NORMAL"
    assert neo4j_dict["from_person_id"] == "P001"
    assert neo4j_dict["to_person_id"] == "P002"


def test_dlq_event_serialization():
    """Verify DLQEvent serializes to structured JSON."""
    dlq = DLQEvent(
        raw_payload='{"bad": "data"}',
        error_reason="Missing transaction_id",
        timestamp="2026-08-15T12:00:00Z",
        source_topic="transactions",
        partition=1,
        offset=42,
    )

    json_str = dlq.to_json()
    data = json.loads(json_str)
    assert data["raw_payload"] == '{"bad": "data"}'
    assert data["error_reason"] == "Missing transaction_id"
    assert data["partition"] == 1
    assert data["offset"] == 42


def test_validation_result_structure():
    """Verify ValidationResult wrapper properties."""
    vr = ValidationResult(is_valid=True)
    assert vr.is_valid is True
    assert vr.transaction is None
    assert vr.dlq_event is None
