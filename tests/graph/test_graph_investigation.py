"""
Graph Investigation Endpoints Unit Tests.
Verifies neighborhood queries, filtered suspicious subgraphs, and common counterparty intersections.
"""
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from analytics.src.models import RiskLevel
from backend.app.dependencies import get_graph_service
from backend.app.main import app
from backend.app.models.graph import GraphEdge, GraphNode, GraphPayload
from backend.app.security.jwt import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


def test_graph_neighborhood_and_suspicious_subgraph(client):
    """Verify /api/v1/graph/neighborhood and /api/v1/graph/suspicious-neighborhood."""
    mock_graph_service = MagicMock()
    payload = GraphPayload(
        focal_account_id="A001",
        nodes=[
            GraphNode(id="A001", label="Account A001", type="Account", risk_score=85.0, risk_level=RiskLevel.CRITICAL),
            GraphNode(id="A002", label="Account A002", type="Account", risk_score=75.0, risk_level=RiskLevel.HIGH),
        ],
        edges=[
            GraphEdge(id="tx_1", source="A001", target="A002", type="TRANSFERRED_TO", amount=15000.0),
        ],
        is_truncated=False,
        total_nodes=2,
        total_edges=1,
    )
    mock_graph_service.get_account_subgraph.return_value = payload
    mock_graph_service.get_suspicious_neighborhood.return_value = payload

    app.dependency_overrides[get_graph_service] = lambda: mock_graph_service
    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Neighborhood
        res_nb = client.get("/api/v1/graph/neighborhood/A001?hops=2", headers=headers)
        assert res_nb.status_code == 200
        assert res_nb.json()["focal_account_id"] == "A001"
        assert len(res_nb.json()["nodes"]) == 2

        # 2. Suspicious neighborhood
        res_susp = client.get("/api/v1/graph/suspicious-neighborhood/A001?min_risk=60.0", headers=headers)
        assert res_susp.status_code == 200
        assert res_susp.json()["total_nodes"] == 2
    finally:
        app.dependency_overrides.clear()


def test_common_counterparties_endpoint(client):
    """Verify /api/v1/graph/common-counterparties endpoint returns shared node intersection."""
    mock_graph_service = MagicMock()
    mock_graph_service.get_common_counterparties.return_value = [
        {
            "common_account_id": "A005",
            "risk_score": 75.0,
            "risk_level": "HIGH",
            "tx_with_a": "TX_01",
            "amount_with_a": 10000.0,
            "tx_with_b": "TX_02",
            "amount_with_b": 9500.0,
        }
    ]

    app.dependency_overrides[get_graph_service] = lambda: mock_graph_service
    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/graph/common-counterparties?account_a=A001&account_b=A002", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["account_a"] == "A001"
        assert data["account_b"] == "A002"
        assert data["common_counterparties_count"] == 1
        assert data["data"][0]["common_account_id"] == "A005"
    finally:
        app.dependency_overrides.clear()
