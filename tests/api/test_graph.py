"""
Unit tests for Graph Neighborhood API endpoint.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_neo4j_client
from backend.app.main import app


def test_get_account_subgraph_endpoint():
    """Verify GET /api/v1/accounts/{id}/graph returns nodes and edges payload."""
    mock_neo4j = MagicMock()
    # 1. transfers query
    # 2. meta query
    mock_neo4j.execute_query.side_effect = [
        [
            {
                "source": "A001",
                "target": "A005",
                "tx_id": "TX_001",
                "amount": 8500.0,
                "currency": "USD",
                "timestamp": "2026-09-01T12:00:00+00:00",
            }
        ],
        [
            {
                "account_id": "A005",
                "account_type": "checking",
                "risk_score": 78.5,
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
        response = client.get("/api/v1/accounts/A005/graph?depth=2")
        assert response.status_code == 200
        payload = response.json()["data"]
        assert "nodes" in payload
        assert "edges" in payload
        assert payload["total_nodes"] > 0
        assert payload["total_edges"] > 0
    finally:
        app.dependency_overrides.clear()
