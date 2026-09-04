"""
Tests for FinGraph Alert Prioritization & SLA Engine.
"""
from datetime import datetime, timedelta, timezone
import pytest

from detection.src.models import DetectionType, Severity
from backend.app.models.operations import (
    PriorityLevel,
    SLAStatus,
    TriageStatus,
)
from backend.app.services.alert_prioritization_service import AlertPrioritizationService


def test_alert_prioritization_scoring_and_explainability():
    service = AlertPrioritizationService()

    # Case 1: High risk entity with critical severity
    score, tier, factors, summary = service.calculate_priority(
        alert_id="ALT-1001",
        detection_type=DetectionType.CIRCULAR_FLOW,
        severity=Severity.CRITICAL,
        confidence=0.95,
        entity_risk_score=90.0,
        network_risk_score=85.0,
        total_amount=150000.0,
        anomaly_score=80.0,
        related_alerts_count=3,
    )

    assert 0.0 <= score <= 100.0
    assert score >= 80.0
    assert tier == PriorityLevel.P0_CRITICAL
    assert len(factors) == 4
    assert any(f.factor_name == "Entity Graph Risk" for f in factors)
    assert any(f.factor_name == "Syndicate Network Risk" for f in factors)
    assert any(f.factor_name == "Severity & Financial Impact" for f in factors)
    assert any(f.factor_name == "Behavioral Anomaly & Velocity" for f in factors)
    assert "ALT-1001" in summary

    # Case 2: Low risk entity with low severity
    score_low, tier_low, factors_low, _ = service.calculate_priority(
        alert_id="ALT-1002",
        detection_type=DetectionType.ONE_TO_MANY,
        severity=Severity.LOW,
        confidence=0.5,
        entity_risk_score=10.0,
        network_risk_score=5.0,
        total_amount=500.0,
        anomaly_score=0.0,
        related_alerts_count=0,
    )

    assert score_low < 35.0
    assert tier_low == PriorityLevel.P3_LOW


def test_alert_sla_calculations_and_countdown():
    service = AlertPrioritizationService()
    now = datetime.now(timezone.utc)

    # 1. New P0 Alert created 5 minutes ago -> within SLA (15m SLA)
    created_5m = now - timedelta(minutes=5)
    deadline, status, rem = service.calculate_sla(
        priority_level=PriorityLevel.P0_CRITICAL,
        created_at=created_5m,
        triage_status=TriageStatus.NEW,
        now=now,
    )
    assert status == SLAStatus.WITHIN_SLA
    assert 9.0 <= rem <= 11.0

    # 2. P0 Alert created 13 minutes ago -> AT_RISK (<25% of 15m is 3.75m)
    created_13m = now - timedelta(minutes=13)
    deadline, status, rem = service.calculate_sla(
        priority_level=PriorityLevel.P0_CRITICAL,
        created_at=created_13m,
        triage_status=TriageStatus.NEW,
        now=now,
    )
    assert status == SLAStatus.AT_RISK
    assert 1.0 <= rem <= 3.0

    # 3. P0 Alert created 20 minutes ago -> BREACHED
    created_20m = now - timedelta(minutes=20)
    deadline, status, rem = service.calculate_sla(
        priority_level=PriorityLevel.P0_CRITICAL,
        created_at=created_20m,
        triage_status=TriageStatus.NEW,
        now=now,
    )
    assert status == SLAStatus.BREACHED
    assert rem == 0.0

    # 4. Resolved alert -> RESOLVED
    deadline, status, rem = service.calculate_sla(
        priority_level=PriorityLevel.P0_CRITICAL,
        created_at=created_20m,
        triage_status=TriageStatus.CONFIRMED_FRAUD,
        now=now,
    )
    assert status == SLAStatus.RESOLVED
