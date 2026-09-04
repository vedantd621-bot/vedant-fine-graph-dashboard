"""
Tests for Central Intelligence Orchestrator in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.orchestrator import IntelligenceOrchestrator
from backend.app.intelligence_orchestration.service import IntelligenceOrchestrationService

@pytest.fixture
def orchestrator():
    return IntelligenceOrchestrator()

@pytest.fixture
def service():
    return IntelligenceOrchestrationService()

def test_orchestrator_sub_engines(orchestrator):
    assert orchestrator.correlation_engine is not None
    assert orchestrator.priority_engine is not None
    assert orchestrator.evidence_engine is not None
    assert orchestrator.brief_generator is not None
    assert orchestrator.template_registry is not None
    assert orchestrator.state_machine is not None
    assert orchestrator.task_manager is not None
    assert orchestrator.timeline_engine is not None
    assert orchestrator.related_cases_engine is not None
    assert orchestrator.recommendation_engine is not None

def test_service_lifecycle_and_caching(service):
    brief1 = service.generate_brief("CASE-2026-001")
    brief2 = service.generate_brief("CASE-2026-001")
    assert brief1.brief_id == brief2.brief_id
    
    # Force refresh
    brief3 = service.generate_brief("CASE-2026-001", force_refresh=True)
    assert brief3.brief_id != brief1.brief_id
