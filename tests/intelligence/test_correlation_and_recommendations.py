"""
Alert Correlation, Recommendations, and Investigation Analytics Unit Tests.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from backend.app.dependencies import get_intelligence_service
from backend.app.main import app
from backend.app.models.alerts import AlertSummary
from backend.app.models.intelligence import (
    AlertCorrelation,
    AlertRecommendationItem,
    AlertRecommendationsResponse,
    InvestigationAnalytics,
)
from backend.app.security.jwt import create_access_token
from detection.src.models import AlertStatus, DetectionType, Severity


@pytest.fixture
def client():
    return TestClient(app)


def test_alert_correlation_endpoint(client):
    """Verify GET /api/v1/alerts/{id}/correlated returns correlated cluster alerts."""
    now = datetime.now(timezone.utc)
    mock_intel_service = MagicMock()
    mock_intel_service.correlate_alert.return_value = AlertCorrelation(
        alert_id="ALT-CIRC-01",
        related_alerts_count=2,
        correlated_alerts=[
            AlertSummary(
                alert_id="ALT-CIRC-02",
                detection_type=DetectionType.CIRCULAR_FLOW,
                severity=Severity.HIGH,
                confidence=0.92,
                primary_account="A002",
                risk_score=85.0,
                status=AlertStatus.OPEN,
                description="Correlated cycle member A002",
                created_at=now,
            )
        ],
        common_entities=["A001", "A002", "A003"],
        common_detectors=["CIRCULAR_FLOW"],
        correlation_strength=0.85,
        correlation_reason="Alert is correlated with 2 related alerts sharing 3 distinct counterparties.",
    )

    app.dependency_overrides[get_intelligence_service] = lambda: mock_intel_service
    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        res = client.get("/api/v1/alerts/ALT-CIRC-01/correlated", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["alert_id"] == "ALT-CIRC-01"
        assert data["related_alerts_count"] == 2
        assert len(data["common_entities"]) == 3
        assert data["correlation_strength"] == 0.85
    finally:
        app.dependency_overrides.clear()


def test_alert_recommendations_endpoint(client):
    """Verify GET /api/v1/alerts/{id}/recommendations returns actionable investigation steps."""
    mock_intel_service = MagicMock()
    mock_intel_service.get_alert_recommendations.return_value = AlertRecommendationsResponse(
        alert_id="ALT-CIRC-01",
        recommendations=[
            AlertRecommendationItem(
                action_type="INSPECT_TRAIL",
                title="Trace Multi-Hop Directed Money Trail",
                description="Inspect multi-hop path topology originating from A001 to identify exit mules.",
                priority=Severity.HIGH,
                target_entity="A001",
                evidence_summary="Detector CIRCULAR_FLOW reported path involving 4 related entities.",
            ),
            AlertRecommendationItem(
                action_type="FREEZE_ACCOUNT",
                title="Execute Precautionary Freeze on A001",
                description="Account risk score (88.5) exceeds containment threshold. Consider immediate freeze.",
                priority=Severity.CRITICAL,
                target_entity="A001",
                evidence_summary="Critical severity alert with elevated risk score 88.5.",
            ),
        ],
    )

    app.dependency_overrides[get_intelligence_service] = lambda: mock_intel_service
    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        res = client.get("/api/v1/alerts/ALT-CIRC-01/recommendations", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["alert_id"] == "ALT-CIRC-01"
        assert len(data["recommendations"]) == 2
        assert data["recommendations"][0]["action_type"] == "INSPECT_TRAIL"
        assert data["recommendations"][1]["action_type"] == "FREEZE_ACCOUNT"
    finally:
        app.dependency_overrides.clear()


def test_investigation_analytics_endpoint(client):
    """Verify GET /api/v1/investigation/analytics returns aggregate platform metrics."""
    mock_intel_service = MagicMock()
    mock_intel_service.get_investigation_analytics.return_value = InvestigationAnalytics(
        cases_by_status={"OPEN": 5, "IN_PROGRESS": 3, "RESOLVED": 2},
        cases_by_priority={"HIGH": 4, "CRITICAL": 3, "MEDIUM": 3},
        alerts_by_detector={"CIRCULAR_FLOW": 4, "FUNNEL": 6, "CHAIN": 2},
        alerts_by_severity={"CRITICAL": 3, "HIGH": 7, "MEDIUM": 2},
        high_risk_entities_count=12,
        active_investigators_count=3,
        top_suspicious_communities=[{"community_id": 1, "syndicate_name": "Circular Alpha", "high_risk_count": 4}],
    )

    app.dependency_overrides[get_intelligence_service] = lambda: mock_intel_service
    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        res = client.get("/api/v1/investigation/analytics", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["cases_by_status"]["OPEN"] == 5
        assert data["high_risk_entities_count"] == 12
        assert data["active_investigators_count"] == 3
    finally:
        app.dependency_overrides.clear()
