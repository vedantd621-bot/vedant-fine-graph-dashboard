"""
Unit tests for Alert API endpoints.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from detection.src.models import DetectionEvidence, DetectionResult, DetectionType, Severity
from backend.app.dependencies import (
    get_detection_engine,
    get_neo4j_client,
    get_risk_engine,
)
from backend.app.main import app
from backend.app.security.jwt import create_access_token


def test_list_alerts_endpoint():
    """Verify GET /api/v1/alerts returns paginated alerts list."""
    mock_neo4j = MagicMock()
    mock_neo4j.execute_query.return_value = []
    mock_det_eng = MagicMock()
    mock_risk_eng = MagicMock()
    mock_risk_eng.gds_manager.extract_graph_features.return_value = {}

    evidence = DetectionEvidence(
        reason_summary="Funnel smurfing",
        metric_name="source_count",
        metric_value=4,
        threshold_value=3,
        source_accounts=["A001", "A002", "A003", "A004"],
        destination_accounts=["A006"],
    )

    mock_det_eng.run_all.return_value = [
        DetectionResult(
            detection_id="DET_FUN_001",
            detection_type=DetectionType.FUNNEL,
            severity=Severity.HIGH,
            confidence=0.92,
            primary_account="A005",
            description="Funnel smurfing on A005",
            evidence=evidence,
            related_accounts=["A001", "A002", "A003", "A004", "A006"],
            transaction_ids=["TX1", "TX2", "TX3", "TX4", "TX5"],
            total_amount=36000.0,
        )
    ]

    from detection.src.models import Alert, AlertStatus
    mock_det_eng.generate_alerts.return_value = [
        Alert(
            alert_id="ALT_FUN_001",
            detection_type=DetectionType.FUNNEL,
            severity=Severity.HIGH,
            confidence=0.92,
            primary_account="A005",
            status=AlertStatus.OPEN,
            description="Funnel smurfing on A005",
            evidence=evidence,
            related_accounts=["A001", "A002", "A003", "A004", "A006"],
            transaction_ids=["TX1", "TX2", "TX3", "TX4", "TX5"],
            total_amount=36000.0,
        )
    ]

    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    app.dependency_overrides[get_detection_engine] = lambda: mock_det_eng
    app.dependency_overrides[get_risk_engine] = lambda: mock_risk_eng
    client = TestClient(app)

    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        response = client.get("/api/v1/alerts?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["alert_id"] == "ALT_FUN_001"
        assert data["data"][0]["primary_account"] == "A005"
        assert data["pagination"]["total_items"] == 1
    finally:
        app.dependency_overrides.clear()


def test_get_alert_detail_and_update_status():
    """Verify GET /api/v1/alerts/{id} and PATCH /api/v1/alerts/{id} status update."""
    mock_neo4j = MagicMock()
    mock_neo4j.execute_query.return_value = []
    mock_det_eng = MagicMock()
    mock_risk_eng = MagicMock()
    mock_risk_eng.gds_manager.extract_graph_features.return_value = {}

    evidence = DetectionEvidence(
        reason_summary="Circular wash trading",
        metric_name="cycle_length",
        metric_value=3,
        threshold_value=2,
    )

    from detection.src.models import Alert, AlertStatus
    mock_det_eng.run_all.return_value = []
    mock_det_eng.generate_alerts.return_value = [
        Alert(
            alert_id="ALT_CYC_001",
            detection_type=DetectionType.CIRCULAR_FLOW,
            severity=Severity.CRITICAL,
            confidence=0.98,
            primary_account="A025",
            status=AlertStatus.OPEN,
            description="Circular flow wash trading",
            evidence=evidence,
            related_accounts=["A026", "A027"],
        )
    ]

    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    app.dependency_overrides[get_detection_engine] = lambda: mock_det_eng
    app.dependency_overrides[get_risk_engine] = lambda: mock_risk_eng
    client = TestClient(app)

    try:
        token = create_access_token({"sub": "usr_inv", "username": "investigator", "role": "INVESTIGATOR"})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Get Detail
        res = client.get("/api/v1/alerts/ALT_CYC_001", headers=headers)
        assert res.status_code == 200
        detail = res.json()
        assert detail["alert_id"] == "ALT_CYC_001"
        assert detail["status"] == "OPEN"

        # 2. Patch Status to INVESTIGATING
        patch_res = client.patch(
            "/api/v1/alerts/ALT_CYC_001",
            json={"status": "INVESTIGATING", "notes": "Investigating node relationships"},
            headers=headers,
        )
        assert patch_res.status_code == 200
        updated = patch_res.json()
        assert updated["status"] == "INVESTIGATING"
    finally:
        app.dependency_overrides.clear()
