"""
Unit tests for Early Warning rules and investigator state transitions.
"""
import pytest
from backend.app.early_warning.models import (
    EarlyWarningSeverity,
    EarlyWarningStatus,
    WarningActionRecommendation,
)
from backend.app.early_warning.rules import EarlyWarningRulesEngine
from backend.app.early_warning.service import EarlyWarningService


def test_early_warning_rules_evaluation():
    rules_engine = EarlyWarningRulesEngine()

    networks = [
        {"network_id": "NET-SURGE", "growth_rate": 35.0, "risk_score": 88.0, "exposure": 120000.0},
    ]
    accounts = [
        {"account_id": "A-ANOMALY", "risk_score": 85.0, "anomaly_score": 80.0},
    ]

    warnings = rules_engine.evaluate_warnings(networks, accounts)
    assert len(warnings) >= 2

    net_warn = next(w for w in warnings if w.entity_type == "NETWORK")
    assert net_warn.severity == EarlyWarningSeverity.CRITICAL
    assert net_warn.recommended_action == WarningActionRecommendation.REVIEW_NETWORK

    acc_warn = next(w for w in warnings if w.entity_type == "ACCOUNT")
    assert acc_warn.severity == EarlyWarningSeverity.HIGH
    assert acc_warn.recommended_action == WarningActionRecommendation.REVIEW_ACCOUNT


def test_early_warning_lifecycle_and_audit():
    service = EarlyWarningService()

    w_id = "WARN-2026-001"

    # 1. Acknowledge
    w_ack = service.acknowledge_warning(
        warning_id=w_id,
        actor_id="usr_inv_002",
        actor_name="investigator",
        notes="Investigator acknowledged warning",
    )
    assert w_ack.status == EarlyWarningStatus.ACKNOWLEDGED
    assert w_ack.acknowledged_by == "investigator"

    # 2. Escalate
    w_esc = service.escalate_warning(
        warning_id=w_id,
        actor_id="usr_inv_002",
        actor_name="investigator",
        notes="Escalated to syndicate case",
    )
    assert w_esc.status == EarlyWarningStatus.ESCALATED

    # 3. Dismiss
    w_dis = service.dismiss_warning(
        warning_id=w_id,
        actor_id="usr_inv_002",
        actor_name="investigator",
        notes="Resolved and dismissed",
    )
    assert w_dis.status == EarlyWarningStatus.DISMISSED


def test_enterprise_threat_and_forecast_scoring():
    service = EarlyWarningService()

    threat = service.calculate_enterprise_threat_level()
    assert 0.0 <= threat.score <= 100.0
    assert len(threat.drivers) >= 1

    forecast = service.forecast_enterprise_risk()
    assert forecast.current_threat_score == threat.score
    assert forecast.forecast_1h >= 0.0
    assert forecast.confidence >= 0.85
