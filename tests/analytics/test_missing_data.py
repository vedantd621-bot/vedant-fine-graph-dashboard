"""
Unit tests for handling missing data, isolated accounts, and empty detections without exceptions.
"""
from unittest.mock import MagicMock
import pytest

from analytics.src.models import GraphFeatures, RiskLevel
from analytics.src.risk_engine import ExplainableRiskEngine


def test_isolated_account_with_zero_transactions():
    """Verify accounts with 0 transactions and 0 degree produce a clean LOW risk result."""
    mock_client = MagicMock()
    engine = ExplainableRiskEngine(client=mock_client)

    zero_feats = GraphFeatures(
        account_id="A_ISOLATED",
        pagerank=0.0,
        wcc_id=None,
        louvain_community_id=None,
        in_degree=0,
        out_degree=0,
        total_degree=0,
        community_size=1,
        total_volume=0.0,
    )

    risk_score = engine.calculate_account_risk("A_ISOLATED", zero_feats, detections=[])

    assert risk_score.account_id == "A_ISOLATED"
    assert risk_score.score == 0.0
    assert risk_score.risk_level == RiskLevel.LOW
    assert risk_score.rule_subscore == 0.0
    assert risk_score.graph_subscore == 0.0
    assert len(risk_score.reasons) == 1
    assert "Normal transactional baseline" in risk_score.reasons[0]


def test_missing_gds_properties_fallback():
    """Verify accounts with None/null GDS values calculate graph subscore via degrees."""
    mock_client = MagicMock()
    engine = ExplainableRiskEngine(client=mock_client)

    fallback_feats = GraphFeatures(
        account_id="A_FALLBACK",
        pagerank=0.0,
        wcc_id=None,
        louvain_community_id=None,
        in_degree=2,
        out_degree=1,
        total_degree=3,
        community_size=1,
        total_volume=5000.0,
    )

    risk_score = engine.calculate_account_risk("A_FALLBACK", fallback_feats, detections=[])

    assert risk_score.account_id == "A_FALLBACK"
    assert risk_score.graph_subscore > 0.0
    assert risk_score.score > 0.0
    assert risk_score.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
