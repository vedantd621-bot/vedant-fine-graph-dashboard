"""
Unit tests for Pattern Discovery and Structural Similarity comparisons.
"""
import pytest
from backend.app.pattern_discovery.models import (
    DiscoveredPattern,
    PatternType,
)
from backend.app.pattern_discovery.service import PatternDiscoveryService
from backend.app.pattern_discovery.similarity import PatternSimilarityEngine


def test_pattern_similarity_scoring():
    engine = PatternSimilarityEngine()

    p1 = DiscoveredPattern(
        pattern_id="P1",
        name="Circular Loop 1",
        pattern_type=PatternType.CIRCULAR_LOOP,
        frequency=5,
        confidence=0.95,
        risk_score=90.0,
        affected_entities=["A1", "A2", "A3"],
        financial_exposure=100000.0,
        explanation="Loop 1",
        supporting_signals=["Signal A", "Signal B"],
    )

    p2 = DiscoveredPattern(
        pattern_id="P2",
        name="Circular Loop 2",
        pattern_type=PatternType.CIRCULAR_LOOP,
        frequency=8,
        confidence=0.92,
        risk_score=85.0,
        affected_entities=["A2", "A3", "A4"],
        financial_exposure=120000.0,
        explanation="Loop 2",
        supporting_signals=["Signal B", "Signal C"],
    )

    sim = engine.calculate_similarity(p1, p2)
    assert 0.0 <= sim.similarity_score <= 1.0
    assert sim.similarity_score > 0.50
    assert "A2" in sim.shared_entities
    assert "Signal B" in sim.shared_signals
    assert "similarity index" in sim.explanation.lower()


def test_pattern_service_queries():
    service = PatternDiscoveryService()

    patterns = service.list_patterns()
    assert len(patterns) >= 2

    p_detail = service.get_pattern("PAT-CIRCULAR-01")
    assert p_detail.pattern_type == PatternType.CIRCULAR_LOOP

    similar_list = service.get_similar_patterns("PAT-CIRCULAR-01")
    assert len(similar_list) >= 1
