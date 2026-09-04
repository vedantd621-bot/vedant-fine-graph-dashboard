"""
Unit tests for Executive Dashboard summary and distribution endpoints.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import (
    get_detection_engine,
    get_neo4j_client,
    get_risk_engine,
)
from backend.app.main import app
from backend.app.security.jwt import create_access_token


def test_dashboard_summary_and_distribution_endpoints():
    """Verify GET /api/v1/dashboard/summary and /risk-distribution."""
    mock_neo4j = MagicMock()

    def mock_query(cypher, params=None):
        if "count(a)" in cypher or "count(DISTINCT a)" in cypher or "Account" in cypher and "count" in cypher:
            return [{"total_accounts": 59}]
        if "TRANSFERRED_TO" in cypher:
            return [{"total_tx": 29, "total_transactions": 29, "total_vol": 250000.0, "total_volume": 250000.0}]
        return []

    mock_neo4j.execute_query.side_effect = mock_query

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

        # 1. Summary
        sum_res = client.get("/api/v1/dashboard/summary", headers=headers)
        assert sum_res.status_code == 200
        sum_data = sum_res.json()
        assert sum_data["total_accounts"] == 59
        assert sum_data["total_transactions"] == 29

        # 2. Risk distribution
        dist_res = client.get("/api/v1/dashboard/risk-distribution", headers=headers)
        assert dist_res.status_code == 200
        dist_data = dist_res.json()
        assert "total_accounts" in dist_data
        assert "critical" in dist_data
    finally:
        app.dependency_overrides.clear()
