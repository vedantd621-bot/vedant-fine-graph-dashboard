"""
Tests for Cross-Alert Correlation Engine in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.correlation import CrossAlertCorrelationEngine
from backend.app.intelligence_orchestration.models import CorrelationReason

@pytest.fixture
def engine():
    return CrossAlertCorrelationEngine()

def test_correlate_alert_multi_signal(engine):
    group = engine.correlate_alert("ALT-CIRC-01")
    assert group.group_id.startswith("grp_")
    assert group.primary_alert_id == "ALT-CIRC-01"
    assert len(group.correlated_alert_ids) >= 2
    assert group.correlation_score >= 0.0 and group.correlation_score <= 1.0
    assert CorrelationReason.SHARED_ACCOUNT in group.reasons
    assert CorrelationReason.SHARED_DEVICE in group.reasons
    assert "shared_account" in group.shared_signals
    assert "shared_device_fingerprint" in group.shared_signals
    assert "ALT-CIRC-01" in group.explanation
