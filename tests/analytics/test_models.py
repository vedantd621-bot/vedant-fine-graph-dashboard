"""
Unit tests for GDS Analytics and Explainable Risk Models.
"""
from datetime import datetime, timezone
import pytest

from analytics.src.models import (
    GraphFeatures,
    RiskAssessment,
    RiskLevel,
    RiskScore,
    RuleSignals,
)


def test_graph_features_model_instantiation():
    """Verify GraphFeatures model structure and defaults."""
    feats = GraphFeatures(
        account_id="A005",
        pagerank=0.185,
        wcc_id=1,
        louvain_community_id=3,
        in_degree=4,
        out_degree=1,
        total_degree=5,
        community_size=6,
        total_volume=71280.0,
    )

    assert feats.account_id == "A005"
    assert feats.pagerank == 0.185
    assert feats.total_degree == 5
    assert feats.community_size == 6
    assert feats.total_volume == 71280.0


def test_rule_signals_model():
    """Verify RuleSignals tracking active detection flags."""
    signals = RuleSignals(
        account_id="A005",
        funnel_flag=True,
        circular_flag=False,
        layered_flag=False,
        one_to_many_flag=False,
        chain_flag=False,
        high_degree_flag=True,
        active_detections_count=2,
        raw_rule_score=35.0,
        detection_types=["FUNNEL", "HIGH_DEGREE"],
    )

    assert signals.funnel_flag is True
    assert signals.high_degree_flag is True
    assert signals.active_detections_count == 2
    assert signals.raw_rule_score == 35.0


def test_risk_score_model_serialization():
    """Verify RiskScore model and dictionary dumping."""
    feats = GraphFeatures(account_id="A025", pagerank=0.09, total_degree=2)
    signals = RuleSignals(account_id="A025", circular_flag=True, raw_rule_score=30.0, active_detections_count=1)

    r_score = RiskScore(
        account_id="A025",
        score=78.5,
        risk_level=RiskLevel.CRITICAL,
        rule_subscore=30.0,
        graph_subscore=65.0,
        model_version="rule-gds-v1",
        features=feats,
        rule_signals=signals,
        reasons=["Account participates in a closed circular wash-trading loop."],
    )

    assert r_score.score == 78.5
    assert r_score.risk_level == RiskLevel.CRITICAL
    d = r_score.model_dump()
    assert d["account_id"] == "A025"
    assert len(d["reasons"]) == 1
