"""
Unit tests for Forensic Investigation & Search API endpoints.
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


def test_money_trail_and_search_endpoints():
    """Verify GET /api/v1/investigation/money-trail and /search."""
    mock_neo4j = MagicMock()
    # 1. Money trail query mock
    # 2. Search accounts query
    # 3. Search tx query
    mock_neo4j.execute_query.side_effect = [
        # money trail
        [
            {
                "path_nodes": ["A001", "A005", "A006"],
                "path_len": 2,
                "tx_ids": ["TX1", "TX2"],
                "amounts": [8500.0, 36000.0],
                "scenario_id": "SC_FUNNEL_01",
            }
        ],
        # search accounts
        [],
        # search tx
        [{"tx_id": "TX_FUN_001"}],
    ]

    mock_det_eng = MagicMock()
    mock_det_eng.run_all.return_value = []
    mock_det_eng.generate_alerts.return_value = []

    mock_risk_eng = MagicMock()
    mock_risk_eng.calculate_all_risks.return_value = []

    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    app.dependency_overrides[get_detection_engine] = lambda: mock_det_eng
    app.dependency_overrides[get_risk_engine] = lambda: mock_risk_eng
    client = TestClient(app)

    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Money trail
        trail_res = client.get("/api/v1/investigation/money-trail?from_account=A001&to_account=A006", headers=headers)
        assert trail_res.status_code == 200
        trail_data = trail_res.json()["data"]
        assert len(trail_data) == 1
        assert trail_data[0]["origin"] == "A001"
        assert trail_data[0]["destination"] == "A006"
        assert trail_data[0]["hop_count"] == 2

        # 2. Search
        search_res = client.get("/api/v1/investigation/search?q=TX_FUN", headers=headers)
        assert search_res.status_code == 200
        search_data = search_res.json()["data"]
        assert "TX_FUN_001" in search_data["transaction_ids"]
    finally:
        app.dependency_overrides.clear()
