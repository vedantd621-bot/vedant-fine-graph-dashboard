"""
Unit tests for ExplainableRiskEngine scoring formula, weights, and combined evaluations.
"""
from unittest.mock import MagicMock
import pytest

from detection.src.models import DetectionEvidence, DetectionResult, DetectionType, Severity
from analytics.src.config import RiskScoringConfig
from analytics.src.gds_manager import GDSManager
from analytics.src.models import GraphFeatures, RiskLevel
from analytics.src.risk_engine import ExplainableRiskEngine


def test_risk_engine_rule_signals_evaluation():
    """Verify evaluation of Phase 6 rule detections for target account."""
    mock_client = MagicMock()
    engine = ExplainableRiskEngine(client=mock_client)

    evidence = DetectionEvidence(
        reason_summary="Funnel aggregation",
        metric_name="source_count",
        metric_value=4,
        threshold_value=3,
        source_accounts=["A001", "A002", "A003", "A004"],
        destination_accounts=["A006"],
    )

    detections = [
        DetectionResult(
            detection_id="DET_1",
            detection_type=DetectionType.FUNNEL,
            severity=Severity.CRITICAL,
            confidence=0.95,
            primary_account="A005",
            description="Funnel smurfing",
            evidence=evidence,
            related_accounts=["A001", "A002", "A003", "A004", "A006"],
        ),
        DetectionResult(
            detection_id="DET_2",
            detection_type=DetectionType.HIGH_DEGREE,
            severity=Severity.HIGH,
            confidence=0.85,
            primary_account="A005",
            description="High degree hub",
            evidence=evidence,
            related_accounts=[],
        ),
    ]

    # Evaluate Primary Account A005 (Funnel +25, HighDegree +10 = 35.0 raw points)
    signals = engine.evaluate_rule_signals("A005", detections)
    assert signals.funnel_flag is True
    assert signals.high_degree_flag is True
    assert signals.circular_flag is False
    assert signals.active_detections_count == 2
    assert signals.raw_rule_score == 35.0

    # Evaluate Related Account A001 (participates in Funnel = 25.0 raw points)
    signals_related = engine.evaluate_rule_signals("A001", detections)
    assert signals_related.funnel_flag is True
    assert signals_related.raw_rule_score == 25.0


def test_risk_engine_composite_score_calculation():
    """Verify combined scoring formula: (Rule * 0.60) + (Graph * 0.40)."""
    mock_client = MagicMock()
    config = RiskScoringConfig(rule_weight=0.60, graph_weight=0.40)
    engine = ExplainableRiskEngine(client=mock_client, config=config)

    feats = GraphFeatures(
        account_id="A005",
        pagerank=0.60,
        total_degree=5,
        community_size=6,
        total_volume=71280.0,
    )

    evidence = DetectionEvidence(
        reason_summary="Funnel aggregation",
        metric_name="source_count",
        metric_value=4,
        threshold_value=3,
    )

    detections = [
        DetectionResult(
            detection_id="DET_1",
            detection_type=DetectionType.FUNNEL,
            severity=Severity.CRITICAL,
            confidence=0.95,
            primary_account="A005",
            description="Funnel smurfing",
            evidence=evidence,
            related_accounts=["A001", "A002", "A003", "A004", "A006"],
        ),
        DetectionResult(
            detection_id="DET_2",
            detection_type=DetectionType.HIGH_DEGREE,
            severity=Severity.HIGH,
            confidence=0.85,
            primary_account="A005",
            description="High degree hub",
            evidence=evidence,
        ),
    ]

    risk_score = engine.calculate_account_risk("A005", feats, detections)

    assert risk_score.account_id == "A005"
    assert risk_score.rule_subscore == 35.0
    assert risk_score.graph_subscore > 50.0
    assert risk_score.score >= 40.0
    assert risk_score.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert len(risk_score.reasons) >= 2
