"""
Tests for SLA Summary, Time-Series Trends, and Detector Confirmation Rates.
"""
from datetime import datetime, timezone
import pytest

from backend.app.services.alert_prioritization_service import AlertPrioritizationService
from backend.app.services.operations_service import OperationsService


class MockDetectionEngine:
    def run_all(self):
        return []
    def generate_alerts(self, detections):
        return []


class MockRiskEngine:
    class MockGDS:
        def extract_graph_features(self, accs):
            return {}
    gds_manager = MockGDS()


class MockCaseService:
    def list_cases(self, page=1, page_size=100):
        return [], 0


class MockNetworkService:
    def list_networks(self, page=1, page_size=100):
        return [], 0


def test_sla_summary_and_fraud_trends():
    prioritization = AlertPrioritizationService()
    service = OperationsService(
        client=None,
        detection_engine=MockDetectionEngine(),
        risk_engine=MockRiskEngine(),
        account_service=None,
        alert_service=None,
        case_service=MockCaseService(),
        network_service=MockNetworkService(),
        prioritization_service=prioritization,
    )

    sla_sum = service.get_sla_summary()
    assert sla_sum.compliance_rate >= 0.0

    trends_hourly = service.get_fraud_trends(interval="hourly", days=1)
    assert trends_hourly.interval == "hourly"
    assert len(trends_hourly.points) > 0

    trends_daily = service.get_fraud_trends(interval="daily", days=7)
    assert trends_daily.interval == "daily"
    assert len(trends_daily.points) > 0

    detectors = service.get_detector_performance()
    assert len(detectors.detectors) > 0
    assert "distinct from ML precision/recall" in detectors.disclaimer
