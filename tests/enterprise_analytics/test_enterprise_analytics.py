"""
Tests for Enterprise Analytics Engine, KPIs, Posture & Trends.
"""
import pytest
from backend.app.enterprise_analytics.models import TrendWindow
from backend.app.enterprise_analytics.service import EnterpriseAnalyticsService


@pytest.fixture
def service():
    return EnterpriseAnalyticsService()


def test_enterprise_kpi_bundle(service):
    bundle = service.get_kpi_bundle(tenant_id="tnt_test")
    assert bundle.tenant_id == "tnt_test"
    assert bundle.fraud.fraud_rate > 0.0
    assert bundle.financial.prevented_loss > 0.0
    assert bundle.operations.sla_compliance_rate > 0.90
    assert bundle.detection.precision_proxy > 0.70
    assert bundle.network.active_fraud_networks > 0
    assert 0.0 <= bundle.posture.posture_score <= 100.0
    assert len(bundle.insights) >= 2
    assert len(bundle.anomalies) >= 1


def test_fraud_trends_generation(service):
    # Daily trends
    daily_trends = service.get_fraud_trends("tnt_test", window=TrendWindow.DAILY, periods=7)
    assert len(daily_trends) == 7
    for t in daily_trends:
        assert t.window == TrendWindow.DAILY
        assert t.confidence >= 0.90
        assert t.exposure >= 0.0

    # Hourly trends
    hourly_trends = service.get_fraud_trends("tnt_test", window=TrendWindow.HOURLY, periods=5)
    assert len(hourly_trends) == 5
    assert hourly_trends[0].window == TrendWindow.HOURLY


def test_executive_posture_and_drivers(service):
    posture = service.get_executive_posture(tenant_id="tnt_acme")
    assert posture.tenant_id == "tnt_acme"
    assert posture.threat_level in ["MINIMAL", "LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert len(posture.positive_drivers) > 0
    assert len(posture.negative_drivers) > 0
    assert len(posture.executive_summary) > 20


def test_kpi_anomalies_detection(service):
    anomalies = service.get_kpi_anomalies(tenant_id="tnt_test")
    assert len(anomalies) > 0
    for a in anomalies:
        assert a.deviation > 20.0
        assert a.baseline > 0.0
        assert a.current > a.baseline
