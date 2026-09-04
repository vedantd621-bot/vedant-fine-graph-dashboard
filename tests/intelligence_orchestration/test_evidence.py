"""
Tests for Evidence Ranking & Weighting Engine in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.evidence import EvidenceRankingEngine
from backend.app.intelligence_orchestration.models import EvidenceStrength, EvidenceCategory

@pytest.fixture
def evidence_engine():
    return EvidenceRankingEngine()

def test_rank_evidence_for_case(evidence_engine):
    evidence = evidence_engine.rank_evidence_for_case("CASE-2026-001")
    assert len(evidence) >= 5
    
    strong_items = [e for e in evidence if e.strength == EvidenceStrength.STRONG]
    moderate_items = [e for e in evidence if e.strength == EvidenceStrength.MODERATE]
    weak_items = [e for e in evidence if e.strength == EvidenceStrength.WEAK]
    
    assert len(strong_items) >= 2
    assert len(moderate_items) >= 2
    assert len(weak_items) >= 1
    
    for item in evidence:
        assert item.evidence_id.startswith("evi_")
        assert item.confidence >= 0.0 and item.confidence <= 1.0
        assert item.source != ""
        assert item.explanation != ""
