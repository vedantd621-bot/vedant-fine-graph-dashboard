"""
Tests for Advisory Recommendation Engine in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.recommendations import InvestigationRecommendationEngine
from backend.app.intelligence_orchestration.models import PriorityBand

@pytest.fixture
def rec_engine():
    return InvestigationRecommendationEngine()

def test_generate_recommendations(rec_engine):
    recs = rec_engine.generate_recommendations("CASE-2026-001")
    assert len(recs) >= 3
    
    action_types = [r.action_type for r in recs]
    assert "ACCOUNT_HOLD" in action_types
    assert "INFRASTRUCTURE_AUDIT" in action_types
    assert "CAMPAIGN_LINK" in action_types
    
    for r in recs:
        assert r.recommendation_id.startswith("irec_")
        assert r.confidence >= 0.8
        assert r.priority in [PriorityBand.CRITICAL, PriorityBand.HIGH, PriorityBand.MEDIUM]
        assert r.is_actioned is False
        assert len(r.supporting_evidence) >= 2
