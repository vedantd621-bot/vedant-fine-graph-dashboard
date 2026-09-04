"""
Tests for Related-Case Discovery Engine in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.related_cases import RelatedCaseDiscoveryEngine

@pytest.fixture
def discovery_engine():
    return RelatedCaseDiscoveryEngine()

def test_discover_related_cases(discovery_engine):
    cases = discovery_engine.discover_related_cases("CASE-2026-001")
    assert len(cases) >= 2
    
    top = cases[0]
    assert top.case_id == "CASE-2026-002"
    assert top.relationship_score >= 0.8
    assert len(top.relationship_reasons) >= 3
    assert "acc_881" in top.shared_entities
