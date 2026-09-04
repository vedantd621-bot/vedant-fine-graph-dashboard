"""
Tests for Unified Forensic Intelligence Timeline in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.timeline import UnifiedTimelineEngine

@pytest.fixture
def timeline_engine():
    return UnifiedTimelineEngine()

def test_generate_timeline(timeline_engine):
    events = timeline_engine.generate_timeline("CASE-2026-001", limit=50)
    assert len(events) >= 6
    
    event_types = [e.event_type for e in events]
    assert "TRANSACTION_INGESTED" in event_types
    assert "CYPHER_MATCH" in event_types
    assert "EARLY_WARNING" in event_types
    assert "ALERT_PRIORITIZED" in event_types
    assert "TASK_ASSIGNED" in event_types
    assert "THREAT_PROPAGATED" in event_types
    
    for ev in events:
        assert ev.event_id.startswith("evt_")
        assert ev.title != ""
        assert ev.source != ""
        assert len(ev.entity_refs) > 0
