"""
Unit tests for Dashboard Analytics API endpoints.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals
from backend.app.dependencies import (
    get_detection_engine,
    get_neo4j_client,
    get_risk_engine,
)
from backend.app.main import app


def test_dashboard_summary_and_distribution_endpoints():
    """Verify GET /api/v1/dashboard/summary and /risk-distribution."""
    mock_neo4j = MagicMock()
    mock_neo4j.execute_query.side_effect = [
        # 1. get_summary aggregates
        [{"total_accounts": 30, "total_transactions": 29, "total_volume": 150000.0}],
        # 2. list_accounts metadata query
        [{"account_id": "A001", "account_type": "checking"}],
        # 3. get_risk_distribution list_accounts metadata query
        [{"account_id": "A001", "account_type": "checking"}],
    ]

    mock_risk_eng = MagicMock()
    feats = GraphFeatures(account_id="A001", pagerank=0.1, total_degree=2, total_volume=5000.0)
    signals = RuleSignals(account_id="A001", raw_rule_score=0.0)
    mock_risk_eng.calculate_all_risks.return_value = [
        RiskScore(
            account_id="A001",
            score=10.0,
            risk_level=RiskLevel.LOW,
            rule_subscore=0.0,
            graph_subscore=10.0,
            features=feats,
            rule_signals=signals,
        )
    ]

    mock_det_eng = MagicMock()
    mock_det_eng.run_all.return_value = []
    mock_det_eng.generate_alerts.return_value = []

    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    app.dependency_overrides[get_risk_engine] = lambda: mock_risk_eng
    app.dependency_overrides[get_detection_engine] = lambda: mock_det_eng
    client = TestClient(app)

    try:
        # 1. Summary
        sum_res = client.get("/api/v1/dashboard/summary")
        assert sum_res.status_code == 200
        sum_data = sum_res.json()["data"]
        assert sum_data["total_accounts"] == 30
        assert sum_data["total_transactions"] == 29
        assert sum_data["total_transaction_volume"] == 150000.0

        # 2. Risk Distribution
        dist_res = client.get("/api/v1/dashboard/risk-distribution")
        assert dist_res.status_code == 200
        dist_data = dist_res.json()["data"]
        assert dist_data["low"] == 1
        assert dist_data["critical"] == 0
    finally:
        app.dependency_overrides.clear()
