"""
Tests for Investigator Assignment, Workload Aggregation & Bulk Operations.
"""
from datetime import datetime, timezone
import pytest

from backend.app.models.operations import (
    PriorityLevel,
    TriageStatus,
)
from backend.app.security.audit import AuditService
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


def test_investigator_workload_aggregation():
    prioritization = AlertPrioritizationService()
    audit = AuditService()
    service = OperationsService(
        client=None,
        detection_engine=MockDetectionEngine(),
        risk_engine=MockRiskEngine(),
        account_service=None,
        alert_service=None,
        case_service=MockCaseService(),
        network_service=MockNetworkService(),
        prioritization_service=prioritization,
        audit_service=audit,
    )

    workload_resp = service.get_investigator_workloads()
    assert len(workload_resp.investigators) >= 3
    for inv in workload_resp.investigators:
        assert inv.username is not None
        assert inv.assigned_alerts >= 0
        assert inv.open_cases >= 0


def test_bulk_operations_validation():
    prioritization = AlertPrioritizationService()
    audit = AuditService()
    service = OperationsService(
        client=None,
        detection_engine=MockDetectionEngine(),
        risk_engine=MockRiskEngine(),
        account_service=None,
        alert_service=None,
        case_service=MockCaseService(),
        network_service=MockNetworkService(),
        prioritization_service=prioritization,
        audit_service=audit,
    )

    # Empty alerts list bulk test
    res = service.bulk_triage_alerts(
        alert_ids=["NONEXISTENT_1", "NONEXISTENT_2"],
        new_status=TriageStatus.CLOSED,
        user_id="usr_admin",
        username="admin",
    )
    assert res.failed_count == 2
    assert res.success_count == 0
