"""
Unit tests for Account API endpoints and simulated freeze action.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals
from backend.app.dependencies import get_neo4j_client, get_risk_engine
from backend.app.main import app
from backend.app.security.jwt import create_access_token


def test_list_accounts_endpoint():
    """Verify GET /api/v1/accounts returns account list with risk features."""
    mock_neo4j = MagicMock()
    mock_neo4j.execute_query.return_value = [
        {
            "account_id": "A005",
            "account_type": "checking",
            "owner_id": "P005",
            "owner_name": "Test Mule",
            "bank_id": "B01",
            "bank_name": "Apex Global Bank",
        }
    ]

    mock_risk_eng = MagicMock()
    feats = GraphFeatures(account_id="A005", pagerank=0.55, total_degree=5, total_volume=71280.0)
    signals = RuleSignals(account_id="A005", funnel_flag=True, raw_rule_score=25.0)
    mock_risk_eng.calculate_all_risks.return_value = [
        RiskScore(
            account_id="A005",
            score=78.5,
            risk_level=RiskLevel.CRITICAL,
            rule_subscore=25.0,
            graph_subscore=70.0,
            features=feats,
            rule_signals=signals,
            reasons=["Funnel intermediary mule."],
        )
    ]

    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    app.dependency_overrides[get_risk_engine] = lambda: mock_risk_eng
    client = TestClient(app)

    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        response = client.get("/api/v1/accounts?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["account_id"] == "A005"
        assert data["data"][0]["risk_score"] == 78.5
        assert data["data"][0]["risk_level"] == "CRITICAL"
    finally:
        app.dependency_overrides.clear()


def test_account_transactions_and_freeze_toggle():
    """Verify GET /api/v1/accounts/{id}/transactions and POST /api/v1/accounts/{id}/freeze."""
    mock_neo4j = MagicMock()
    mock_neo4j.execute_query.side_effect = [
        # Metadata query for get_account_by_id
        [{"account_id": "A005", "is_frozen": False, "account_type": "checking", "owner_id": "P01", "owner_name": "Alice", "bank_id": "B01", "bank_name": "Apex Bank"}],
        # Transactions query
        [
            {
                "transaction_id": "TX_FUN_001",
                "direction": "INCOMING",
                "counterparty": "A001",
                "amount": 8500.0,
                "currency": "USD",
                "timestamp": "2026-09-01T10:00:00+00:00",
                "transaction_type": "transfer",
                "scenario_id": "SC_FUNNEL_01",
                "channel": "online",
            }
        ],
        # Metadata query for freeze get_account_by_id
        [{"account_id": "A005", "is_frozen": False, "account_type": "checking", "owner_id": "P01", "owner_name": "Alice", "bank_id": "B01", "bank_name": "Apex Bank"}],
    ]

    mock_risk = MagicMock()
    mock_risk.gds_manager.extract_graph_features.return_value = {"A005": GraphFeatures(account_id="A005")}
    mock_risk.calculate_account_risk.return_value = RiskScore(
        account_id="A005",
        score=50.0,
        risk_level=RiskLevel.MEDIUM,
        rule_subscore=20.0,
        graph_subscore=30.0,
        features=GraphFeatures(account_id="A005"),
        rule_signals=RuleSignals(account_id="A005"),
    )

    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    app.dependency_overrides[get_risk_engine] = lambda: mock_risk
    client = TestClient(app)

    try:
        inv_token = create_access_token({"sub": "usr_inv", "username": "investigator", "role": "INVESTIGATOR"})
        headers = {"Authorization": f"Bearer {inv_token}"}

        # 1. Transactions
        tx_res = client.get("/api/v1/accounts/A005/transactions", headers=headers)
        assert tx_res.status_code == 200
        tx_data = tx_res.json()
        assert len(tx_data["data"]) == 1
        assert tx_data["data"][0]["transaction_id"] == "TX_FUN_001"
        assert tx_data["data"][0]["counterparty"] == "A001"

        # 2. Freeze Account
        freeze_res = client.post(
            "/api/v1/accounts/A005/freeze",
            json={"freeze": True, "reason": "Suspected mule account"},
            headers=headers,
        )
        assert freeze_res.status_code == 200
        freeze_data = freeze_res.json()
        assert freeze_data["is_frozen"] is True
        assert freeze_data["action"] == "FROZEN"
    finally:
        app.dependency_overrides.clear()
