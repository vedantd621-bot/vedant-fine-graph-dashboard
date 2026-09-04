"""
Tests for Unified Search and In-App Notifications.
"""
from datetime import datetime, timezone
import pytest

from backend.app.models.notifications import NotificationSeverity, NotificationType
from backend.app.security.models import Role
from backend.app.services.alert_prioritization_service import AlertPrioritizationService
from backend.app.services.notification_service import NotificationService
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


class MockAccountService:
    def list_accounts(self, page=1, page_size=100):
        return [], 0


def test_in_app_notifications_lifecycle():
    notif_service = NotificationService()

    # Create notification targeted to investigator role
    notif = notif_service.create_notification(
        type=NotificationType.CRITICAL_ALERT,
        title="Critical Syndicate Detected",
        message="P0 Circular ring detected on ACC-9999",
        severity=NotificationSeverity.CRITICAL,
        target_role=Role.INVESTIGATOR,
        resource_type="ALERT",
        resource_id="ALT-9999",
    )

    assert notif.notification_id.startswith("notif_")
    assert not notif.is_read

    # Retrieve notifications for investigator
    res = notif_service.list_user_notifications(user_id="usr_inv_1", user_role=Role.INVESTIGATOR)
    assert res.unread_count >= 1
    assert any(n.notification_id == notif.notification_id for n in res.notifications)

    # Mark as read
    updated = notif_service.mark_as_read(notif.notification_id, user_id="usr_inv_1")
    assert updated.is_read

    # Mark all read
    cnt = notif_service.mark_all_as_read(user_id="usr_inv_1", user_role=Role.INVESTIGATOR)
    assert cnt >= 0


def test_unified_multi_entity_search():
    prioritization = AlertPrioritizationService()
    service = OperationsService(
        client=None,
        detection_engine=MockDetectionEngine(),
        risk_engine=MockRiskEngine(),
        account_service=MockAccountService(),
        alert_service=None,
        case_service=MockCaseService(),
        network_service=MockNetworkService(),
        prioritization_service=prioritization,
    )

    search_res = service.unified_search(query="alice")
    assert search_res.query == "alice"
    assert search_res.total_matches >= 1
    assert any(r.entity_type == "INVESTIGATOR" for r in search_res.results)
