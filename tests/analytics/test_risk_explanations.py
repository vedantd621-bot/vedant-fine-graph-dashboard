"""
Unit tests for Explainable Audit Rationale generation.
"""
from unittest.mock import MagicMock
import pytest

from analytics.src.models import GraphFeatures, RiskLevel, RuleSignals
from analytics.src.risk_engine import ExplainableRiskEngine


def test_reasons_generation_for_circular_and_layered_syndicates():
    """Verify explainable audit bullets generated for complex patterns."""
    mock_client = MagicMock()
    engine = ExplainableRiskEngine(client=mock_client)

    # 1. Circular Flow
    circ_signals = RuleSignals(
        account_id="A025",
        circular_flag=True,
        raw_rule_score=30.0,
        active_detections_count=1,
    )
    circ_feats = GraphFeatures(account_id="A025", total_degree=2, pagerank=0.10)
    circ_reasons = engine.generate_reasons(circ_signals, circ_feats, 45.0, RiskLevel.MEDIUM)
    assert any("circular wash-trading" in r for r in circ_reasons)

    # 2. Layered Network
    lay_signals = RuleSignals(
        account_id="A007",
        layered_flag=True,
        raw_rule_score=30.0,
        active_detections_count=1,
    )
    lay_feats = GraphFeatures(account_id="A007", total_degree=6, pagerank=0.75, community_size=7)
    lay_reasons = engine.generate_reasons(lay_signals, lay_feats, 82.0, RiskLevel.CRITICAL)
    assert any("multi-tier layered syndicate" in r for r in lay_reasons)
    assert any("PageRank centrality" in r for r in lay_reasons)
    assert any("community cluster" in r for r in lay_reasons)


def test_reasons_generation_for_baseline_account():
    """Verify normal accounts receive baseline risk explanation."""
    mock_client = MagicMock()
    engine = ExplainableRiskEngine(client=mock_client)

    norm_signals = RuleSignals(account_id="A099")
    norm_feats = GraphFeatures(account_id="A099", total_degree=1, pagerank=0.05, community_size=1)
    norm_reasons = engine.generate_reasons(norm_signals, norm_feats, 10.0, RiskLevel.LOW)

    assert len(norm_reasons) == 1
    assert "Normal transactional baseline" in norm_reasons[0]
