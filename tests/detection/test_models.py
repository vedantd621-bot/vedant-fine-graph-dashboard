"""
Unit tests for Detection & Alert Models and Fingerprint Deduplication.
"""
from datetime import datetime, timezone
import pytest

from detection.src.models import (
    Alert,
    AlertStatus,
    DetectionEvidence,
    DetectionResult,
    DetectionType,
    Severity,
    generate_fingerprint,
)


def test_detection_result_model_and_evidence():
    """Verify DetectionResult and DetectionEvidence validation and serialization."""
    evidence = DetectionEvidence(
        reason_summary="Intermediary mule account aggregated 4 sources",
        metric_name="source_count",
        metric_value=4,
        threshold_value=3,
        source_accounts=["A1", "A2", "A3", "A4"],
        destination_accounts=["A6"],
        intermediary_accounts=["A5"],
        inflow_amount=35000.0,
        outflow_amount=34500.0,
    )

    result = DetectionResult(
        detection_id="DET_001",
        detection_type=DetectionType.FUNNEL,
        severity=Severity.HIGH,
        confidence=0.92,
        primary_account="A5",
        scenario_id="SC_FUNNEL_01",
        description="Funnel smurfing pattern",
        evidence=evidence,
        related_accounts=["A1", "A2", "A3", "A4", "A6"],
        transaction_ids=["TX1", "TX2", "TX3", "TX4", "TX5"],
        total_amount=35000.0,
        currency="USD",
    )

    assert result.detection_id == "DET_001"
    assert result.severity == Severity.HIGH
    assert result.confidence == 0.92
    assert result.evidence.metric_value == 4
    dict_repr = result.model_dump()
    assert dict_repr["primary_account"] == "A5"


def test_deterministic_fingerprint_generation():
    """Verify fingerprint hashing is deterministic regardless of related accounts order."""
    fp1 = generate_fingerprint("FUNNEL", "A5", ["A1", "A2", "A3", "A4"])
    fp2 = generate_fingerprint("FUNNEL", "A5", ["A4", "A3", "A2", "A1"])
    assert fp1 == fp2
    assert len(fp1) == 16

    fp_diff = generate_fingerprint("CIRCULAR_FLOW", "A5", ["A1", "A2", "A3", "A4"])
    assert fp1 != fp_diff


def test_alert_model_defaults_and_status():
    """Verify Alert model defaults to OPEN status."""
    evidence = DetectionEvidence(
        reason_summary="Cycle detected",
        metric_name="cycle_length",
        metric_value=3,
        threshold_value=2,
    )
    alert = Alert(
        alert_id="ALT_123",
        detection_type=DetectionType.CIRCULAR_FLOW,
        severity=Severity.CRITICAL,
        confidence=0.98,
        primary_account="A25",
        description="Wash trading cycle",
        evidence=evidence,
        related_accounts=["A26", "A27"],
    )

    assert alert.status == AlertStatus.OPEN
    assert alert.severity == Severity.CRITICAL
