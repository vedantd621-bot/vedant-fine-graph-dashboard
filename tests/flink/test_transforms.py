"""
Unit tests for FinGraph Flink Transformations & Validation Logic.
"""
import json
from datetime import datetime, timezone
import pytest

from flink.src.transforms import decode_and_validate, extract_event_timestamp


def test_decode_and_validate_valid_json_payload():
    """Verify valid JSON transaction is normalized into CanonicalTransaction."""
    payload = {
        "transaction_id": "TX_VALID_123",
        "from_account": "A001",
        "to_account": "A002",
        "amount": 2500.00,
        "currency": "USD",
        "timestamp": "2026-08-10T14:30:00Z",
        "scenario_id": "SC_FUNNEL_01",
        "transaction_type": "smurfing",
        "channel": "online",
        "from_person_id": "P001",
        "to_person_id": "P002",
    }
    raw_bytes = json.dumps(payload).encode("utf-8")

    result = decode_and_validate(raw_bytes, topic="transactions", partition=0, offset=10)
    assert result.is_valid is True
    assert result.dlq_event is None
    assert result.transaction is not None

    tx = result.transaction
    assert tx.transaction_id == "TX_VALID_123"
    assert tx.from_account == "A001"
    assert tx.to_account == "A002"
    assert tx.amount == 2500.00
    assert tx.currency == "USD"
    assert tx.scenario_id == "SC_FUNNEL_01"
    assert tx.timestamp.tzinfo == timezone.utc

    epoch_ms = extract_event_timestamp(tx)
    assert epoch_ms > 0


def test_decode_and_validate_missing_transaction_id():
    """Verify missing transaction_id triggers DLQ routing."""
    payload = {
        "from_account": "A001",
        "to_account": "A002",
        "amount": 100.0,
        "timestamp": "2026-08-10T14:30:00Z",
    }
    result = decode_and_validate(json.dumps(payload))
    assert result.is_valid is False
    assert result.transaction is None
    assert result.dlq_event is not None
    assert "transaction_id" in result.dlq_event.error_reason


def test_decode_and_validate_negative_amount():
    """Verify negative or zero amount triggers DLQ routing."""
    payload = {
        "transaction_id": "TX_BAD_AMT",
        "from_account": "A001",
        "to_account": "A002",
        "amount": -500.0,
        "timestamp": "2026-08-10T14:30:00Z",
    }
    result = decode_and_validate(json.dumps(payload))
    assert result.is_valid is False
    assert "strictly positive" in result.dlq_event.error_reason


def test_decode_and_validate_invalid_currency():
    """Verify unsupported currency triggers DLQ routing."""
    payload = {
        "transaction_id": "TX_BAD_CURR",
        "from_account": "A001",
        "to_account": "A002",
        "amount": 100.0,
        "currency": "BITCOIN",
        "timestamp": "2026-08-10T14:30:00Z",
    }
    result = decode_and_validate(json.dumps(payload))
    assert result.is_valid is False
    assert "Unsupported currency" in result.dlq_event.error_reason


def test_decode_and_validate_invalid_json_syntax():
    """Verify malformed JSON syntax triggers DLQ routing."""
    raw_corrupted = b"NOT_JSON_DATA_---"
    result = decode_and_validate(raw_corrupted)
    assert result.is_valid is False
    assert "JSON parsing error" in result.dlq_event.error_reason


def test_decode_and_validate_invalid_timestamp():
    """Verify unparseable timestamp triggers DLQ routing."""
    payload = {
        "transaction_id": "TX_BAD_TS",
        "from_account": "A001",
        "to_account": "A002",
        "amount": 100.0,
        "timestamp": "NOT_A_TIMESTAMP",
    }
    result = decode_and_validate(json.dumps(payload))
    assert result.is_valid is False
    assert "Invalid timestamp format" in result.dlq_event.error_reason
