"""
Unit tests for FinGraph Pydantic V2 Data Models.
"""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from simulator.src.models import (
    Account,
    AccountType,
    Bank,
    Currency,
    Person,
    ScenarioID,
    TransactionEvent,
    TransactionType,
)


def test_valid_transaction_event_serialization():
    """Verify valid TransactionEvent serializes to JSON according to contract."""
    event = TransactionEvent(
        transaction_id="TX10001",
        timestamp=datetime(2026, 8, 9, 10, 0, 0, tzinfo=timezone.utc),
        from_account="A101",
        to_account="A205",
        amount=9900.0,
        currency=Currency.USD,
        from_person="David Vance",
        to_person="Elena Rostova",
        bank="B01",
        transaction_type=TransactionType.CIRCULAR,
        scenario_id=ScenarioID.SC_CIRCULAR_01.value,
        channel="wire",
        status="COMPLETED",
        is_synthetic=True,
    )

    json_str = event.model_dump_json()
    assert "TX10001" in json_str
    assert "9900.0" in json_str or "9900" in json_str
    assert "A101" in json_str
    assert "A205" in json_str
    assert "SC_CIRCULAR_01" in json_str
    assert event.amount == 9900.0
    assert event.timestamp.tzinfo is not None


def test_transaction_event_negative_amount_rejected():
    """Amount <= 0 must fail validation."""
    with pytest.raises(ValidationError):
        TransactionEvent(
            transaction_id="TX10002",
            timestamp=datetime.now(timezone.utc),
            from_account="A101",
            to_account="A205",
            amount=-50.0,  # Invalid
            currency=Currency.USD,
            from_person="Alice",
            to_person="Bob",
            bank="B01",
        )

    with pytest.raises(ValidationError):
        TransactionEvent(
            transaction_id="TX10003",
            timestamp=datetime.now(timezone.utc),
            from_account="A101",
            to_account="A205",
            amount=0.0,  # Invalid
            currency=Currency.USD,
            from_person="Alice",
            to_person="Bob",
            bank="B01",
        )


def test_transaction_event_empty_parties_rejected():
    """Empty from/to account or person strings must fail validation."""
    with pytest.raises(ValidationError):
        TransactionEvent(
            transaction_id="TX10004",
            timestamp=datetime.now(timezone.utc),
            from_account="   ",  # Blank
            to_account="A205",
            amount=100.0,
            from_person="Alice",
            to_person="Bob",
            bank="B01",
        )

    with pytest.raises(ValidationError):
        TransactionEvent(
            transaction_id="TX10005",
            timestamp=datetime.now(timezone.utc),
            from_account="A101",
            to_account="",  # Empty
            amount=100.0,
            from_person="Alice",
            to_person="Bob",
            bank="B01",
        )


def test_extra_fields_forbidden():
    """Ensures schema enforces strict extra='forbid'."""
    with pytest.raises(ValidationError):
        TransactionEvent(
            transaction_id="TX10006",
            timestamp=datetime.now(timezone.utc),
            from_account="A101",
            to_account="A205",
            amount=100.0,
            from_person="Alice",
            to_person="Bob",
            bank="B01",
            unauthorized_field="malicious_payload",  # Extra
        )


def test_naive_timestamp_converted_to_utc():
    """Naive datetime timestamps must automatically be timezone-aware (UTC)."""
    naive_dt = datetime(2026, 8, 9, 10, 0, 0)
    event = TransactionEvent(
        transaction_id="TX10007",
        timestamp=naive_dt,
        from_account="A101",
        to_account="A205",
        amount=150.0,
        from_person="Alice",
        to_person="Bob",
        bank="B01",
    )
    assert event.timestamp.tzinfo is not None
    assert event.timestamp.tzinfo == timezone.utc


def test_account_and_bank_models():
    """Verify Account, Person, and Bank model constraints."""
    bank = Bank(bank_id="B01", name="Apex Global Bank", country="US")
    assert bank.bank_id == "B01"

    person = Person(person_id="P101", name="Alice Johnson")
    assert person.name == "Alice Johnson"

    account = Account(
        account_id="A101",
        account_type=AccountType.CHECKING,
        owner_person_id="P101",
        bank_id="B01",
        risk_score=15.5,
    )
    assert account.account_id == "A101"
    assert account.risk_score == 15.5
    assert not account.is_frozen
