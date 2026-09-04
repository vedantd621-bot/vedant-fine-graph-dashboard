"""
Tests for Automated Investigation Brief Generator in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.brief import InvestigationBriefGenerator
from backend.app.intelligence_orchestration.models import PriorityBand

@pytest.fixture
def generator():
    return InvestigationBriefGenerator()

def test_generate_brief(generator):
    brief = generator.generate_brief("CASE-2026-001")
    assert brief.brief_id.startswith("brf_")
    assert brief.case_or_alert_id == "CASE-2026-001"
    assert brief.priority_assessment.priority_band == PriorityBand.CRITICAL
    assert brief.financial_exposure == 148500.0
    assert len(brief.ranked_evidence) >= 5
    assert len(brief.unified_timeline) >= 3
    assert len(brief.related_cases) >= 1
    assert len(brief.recommended_investigation_steps) >= 2
    assert len(brief.open_questions) >= 3
    assert brief.executive_summary != ""
    assert brief.threat_propagation_summary != ""
