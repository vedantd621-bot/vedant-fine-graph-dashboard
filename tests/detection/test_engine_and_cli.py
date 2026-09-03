"""
Unit tests for DetectionEngine and CLI execution.
"""
from unittest.mock import MagicMock, patch
import pytest

from detection.src.engine import DetectionEngine
from detection.src.models import DetectionEvidence, DetectionResult, DetectionType, Severity


def test_engine_run_all_and_alert_deduplication():
    """Verify DetectionEngine executes all detectors and deduplicates repeated alerts."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = []

    engine = DetectionEngine(client=mock_client, auto_connect=False)

    # 1. Test run_all executes without exceptions
    results = engine.run_all()
    assert isinstance(results, list)

    # 2. Test generate_alerts deduplication
    evidence = DetectionEvidence(
        reason_summary="Cycle test",
        metric_name="cycle_length",
        metric_value=3,
        threshold_value=2,
    )

    det1 = DetectionResult(
        detection_id="DET_1",
        detection_type=DetectionType.CIRCULAR_FLOW,
        severity=Severity.CRITICAL,
        confidence=0.95,
        primary_account="A25",
        description="Wash trading cycle",
        evidence=evidence,
        related_accounts=["A26", "A27"],
    )
    det2 = DetectionResult(
        detection_id="DET_2",
        detection_type=DetectionType.CIRCULAR_FLOW,
        severity=Severity.CRITICAL,
        confidence=0.95,
        primary_account="A25",
        description="Wash trading cycle duplicate",
        evidence=evidence,
        related_accounts=["A27", "A26"],  # Reordered related accounts
    )

    alerts = engine.generate_alerts([det1, det2])
    # The two detections for the same graph topology must produce exactly 1 deduplicated alert
    assert len(alerts) == 1
    assert alerts[0].primary_account == "A25"
    assert alerts[0].detection_type == DetectionType.CIRCULAR_FLOW
