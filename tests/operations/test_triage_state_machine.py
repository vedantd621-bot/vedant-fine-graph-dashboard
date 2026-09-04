"""
Tests for Triage State Machine & Valid Transitions.
"""
from datetime import datetime, timezone
import pytest

from backend.app.models.operations import TriageStatus
from backend.app.services.operations_service import (
    VALID_TRIAGE_TRANSITIONS,
    OperationsService,
)


def test_valid_and_invalid_triage_state_transitions():
    # Verify state machine matrix structure
    assert TriageStatus.NEW in VALID_TRIAGE_TRANSITIONS
    assert TriageStatus.TRIAGED in VALID_TRIAGE_TRANSITIONS[TriageStatus.NEW]
    assert TriageStatus.INVESTIGATING in VALID_TRIAGE_TRANSITIONS[TriageStatus.NEW]
    assert TriageStatus.FALSE_POSITIVE in VALID_TRIAGE_TRANSITIONS[TriageStatus.NEW]
    assert TriageStatus.CLOSED in VALID_TRIAGE_TRANSITIONS[TriageStatus.NEW]

    # Valid transitions from INVESTIGATING
    investigating_allowed = VALID_TRIAGE_TRANSITIONS[TriageStatus.INVESTIGATING]
    assert TriageStatus.CONFIRMED_FRAUD in investigating_allowed
    assert TriageStatus.ESCALATED in investigating_allowed
    assert TriageStatus.FALSE_POSITIVE in investigating_allowed

    # Invalid transitions: CONFIRMED_FRAUD cannot directly become INVESTIGATING
    confirmed_allowed = VALID_TRIAGE_TRANSITIONS[TriageStatus.CONFIRMED_FRAUD]
    assert TriageStatus.INVESTIGATING not in confirmed_allowed
    assert TriageStatus.CLOSED in confirmed_allowed
