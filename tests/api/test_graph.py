"""
Unit tests for Graph Subgraph visualization endpoint.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_neo4j_client, get_risk_engine
from backend.app.main import app
from backend.app.security.jwt import create_access_token


def test_get_account_subgraph_endpoint():
    """Verify GET /api/v1/accounts/{id}/graph returns bounded D3 graph payload."""
    mock_neo4j = MagicMock()
    # Mock relationships and node metadata queries
    mock_neo4j.execute_query.side_effect = [
        # relationships query
        [
            {
                "src_id": "A001",
                "dst_id": "A005",
                "tx_id": "TX_001",
                "amount": 9000.0,
                "scenario_id": "SC_FUNNEL_01",
                "timestamp": "2026-09-01T10:00:00+00:00",
            }
        ],
        # node metadata query
        [
            {
                "account_id": "A005",
                "account_type": "checking",
                "risk_score": 85.0,
                "risk_level": "CRITICAL",
                "owner_id": "P005",
                "owner_name": "Mule Entity",
                "bank_id": "B01",
                "bank_name": "Apex Global Bank",
            },
            {
                "account_id": "A001",
                "account_type": "checking",
                "risk_score": 20.0,
                "risk_level": "LOW",
                "owner_id": "P001",
                "owner_name": "Retail User",
                "bank_id": "B01",
                "bank_name": "Apex Global Bank",
            },
        ],
    ]

    app.dependency_overrides[get_neo4j_client] = lambda: mock_neo4j
    client = TestClient(app)

    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        response = client.get("/api/v1/accounts/A005/graph?depth=2", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "links" in data
        assert len(data["nodes"]) >= 2
        assert any(n["id"] == "A005" for n in data["nodes"])
        assert any(n["id"] == "A001" for n in data["nodes"])
        assert len(data["links"]) >= 1
    finally:
        app.dependency_overrides.clear()
