"""
Unit tests for Risk Score persistence to Neo4j.
"""
from unittest.mock import MagicMock
import pytest

from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals
from analytics.src.risk_engine import ExplainableRiskEngine


def test_persist_risk_scores_batch_execution():
    """Verify persist_risk_scores invokes parameterized UNWIND Cypher query."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{"updated_count": 2}]

    engine = ExplainableRiskEngine(client=mock_client)

    rs1 = RiskScore(
        account_id="A005",
        score=78.5,
        risk_level=RiskLevel.CRITICAL,
        rule_subscore=35.0,
        graph_subscore=70.0,
        features=GraphFeatures(account_id="A005", pagerank=0.55, total_degree=5),
        rule_signals=RuleSignals(account_id="A005"),
        reasons=["Funnel intermediary mule."],
    )
    rs2 = RiskScore(
        account_id="A001",
        score=22.0,
        risk_level=RiskLevel.LOW,
        rule_subscore=10.0,
        graph_subscore=15.0,
        features=GraphFeatures(account_id="A001", pagerank=0.10, total_degree=1),
        rule_signals=RuleSignals(account_id="A001"),
        reasons=["Baseline retail account."],
    )

    count = engine.persist_risk_scores([rs1, rs2])

    assert count == 2
    mock_client.execute_query.assert_called_once()
    query, params = mock_client.execute_query.call_args.args
    assert "UNWIND $batch AS item" in query
    assert len(params["batch"]) == 2
    assert params["batch"][0]["account_id"] == "A005"
    assert params["batch"][0]["risk_score"] == 78.5
    assert params["batch"][0]["risk_level"] == "CRITICAL"


def test_persist_empty_list():
    """Verify persisting empty list returns 0 without database call."""
    mock_client = MagicMock()
    engine = ExplainableRiskEngine(client=mock_client)

    count = engine.persist_risk_scores([])
    assert count == 0
    mock_client.execute_query.assert_not_called()
