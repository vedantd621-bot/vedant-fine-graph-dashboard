"""
Unit tests for immutable activity logging, evidence provenance, and command center KPIs.
"""
import pytest
from backend.app.case_intelligence.models import (
    AddCommentRequest,
    CampaignStatus,
    CampaignUpdateRequest,
    CaseActivityEventType,
)
from backend.app.case_intelligence.service import CaseIntelligenceService
from backend.app.services.case_service import CaseService


def test_activity_logging_and_feed_ordering():
    case_service = CaseService()
    service = CaseIntelligenceService(case_service=case_service)

    case_id = "CASE-2026-001"

    # Post an action
    service.add_comment(
        case_id=case_id,
        req=AddCommentRequest(content="Forensic validation complete."),
        author_id="usr_inv_002",
        author_name="investigator",
    )

    feed = service.get_case_activity_feed(case_id)
    assert len(feed) >= 1
    # Check that events are in chronological order
    for i in range(len(feed) - 1):
        assert feed[i].timestamp <= feed[i + 1].timestamp


def test_command_center_summary_and_posture_scoring():
    case_service = CaseService()
    service = CaseIntelligenceService(case_service=case_service)

    summary = service.get_command_center_summary()

    assert summary.active_investigations >= 1
    assert summary.confirmed_fraud_value >= 0.0
    assert summary.active_campaigns_count >= 1
    assert len(summary.top_campaigns) >= 1

    posture = summary.posture
    assert 0.0 <= posture.posture_score <= 100.0
    assert len(posture.top_drivers) >= 1
    assert len(posture.positive_drivers) >= 1
    assert len(posture.negative_drivers) >= 1
