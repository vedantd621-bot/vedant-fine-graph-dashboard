"""
Unit tests for Autonomous Fraud Intelligence Engine and Adaptive Recommendations.
"""
import pytest
from backend.app.autonomous_intelligence.models import (
    EmergingPatternType,
    GapPriority,
    RecommendationReviewRequest,
    RecommendationStatus,
    RecommendationType,
    VersionStatus,
)
from backend.app.autonomous_intelligence.signals import DetectionGapFinder
from backend.app.autonomous_intelligence.recommendations import AdaptiveRecommendationEngine
from backend.app.autonomous_intelligence.service import AutonomousIntelligenceService
from backend.app.autonomous_intelligence.exceptions import (
    GapNotFoundError,
    InvalidStatusTransitionError,
    RecommendationNotFoundError,
)


def test_detection_gap_finder_discovers_motifs():
    finder = DetectionGapFinder()
    gaps = finder.scan_gaps()
    assert len(gaps) >= 4

    cycle_gap = next(g for g in gaps if g.pattern_type == EmergingPatternType.STRUCTURAL_CYCLE)
    assert cycle_gap.priority == GapPriority.CRITICAL
    assert cycle_gap.uncovered_motif_count > 0
    assert cycle_gap.estimated_financial_exposure > 0
    assert len(cycle_gap.affected_entities) > 0
    assert len(cycle_gap.sample_motifs) > 0


def test_adaptive_recommendation_engine_synthesizes_rules():
    finder = DetectionGapFinder()
    gaps = finder.scan_gaps()
    engine = AdaptiveRecommendationEngine()
    recs = engine.generate_recommendations(gaps)

    assert len(recs) >= len(gaps)
    for rec in recs:
        assert rec.status == RecommendationStatus.PROPOSED
        assert rec.confidence_score >= 0.70
        assert rec.expected_impact_summary
        assert isinstance(rec.suggested_parameters, dict)


def test_autonomous_service_lifecycle_governance():
    service = AutonomousIntelligenceService()
    
    # List initial gaps & recs
    gaps = service.list_gaps()
    assert len(gaps) >= 4
    
    recs = service.list_recommendations()
    assert len(recs) >= 4
    target_rec = recs[0]

    # Propose -> Under Review
    req_review = RecommendationReviewRequest(status=RecommendationStatus.UNDER_REVIEW, notes="Analyst triage")
    rec_reviewed = service.review_recommendation(target_rec.recommendation_id, req_review, reviewer_id="usr_inv_002")
    assert rec_reviewed.status == RecommendationStatus.UNDER_REVIEW
    assert len(rec_reviewed.status_history) == 1

    # Under Review -> Approved
    req_approve = RecommendationReviewRequest(status=RecommendationStatus.APPROVED, notes="Approved for deployment")
    rec_approved = service.review_recommendation(target_rec.recommendation_id, req_approve, reviewer_id="usr_admin_001")
    assert rec_approved.status == RecommendationStatus.APPROVED

    # Approved -> Deployed (Generates new DetectorVersion)
    req_deploy = RecommendationReviewRequest(status=RecommendationStatus.DEPLOYED, notes="Production cutover")
    rec_deployed = service.review_recommendation(target_rec.recommendation_id, req_deploy, reviewer_id="usr_admin_001")
    assert rec_deployed.status == RecommendationStatus.DEPLOYED
    assert rec_deployed.deployed_at is not None

    # Verify detector version created
    versions = service.list_detector_versions()
    assert len(versions) >= 3
    latest_version = versions[0]
    assert latest_version.recommendation_id == target_rec.recommendation_id
    assert latest_version.status == VersionStatus.ACTIVE


def test_autonomous_service_invalid_transition():
    service = AutonomousIntelligenceService()
    recs = service.list_recommendations()
    target_rec = recs[0]

    # PROPOSED directly to DEPLOYED is invalid (must be APPROVED first)
    req_invalid = RecommendationReviewRequest(status=RecommendationStatus.DEPLOYED)
    with pytest.raises(InvalidStatusTransitionError):
        service.review_recommendation(target_rec.recommendation_id, req_invalid, reviewer_id="usr_admin_001")


def test_autonomous_summary_metrics():
    service = AutonomousIntelligenceService()
    summary = service.get_summary()
    assert summary.active_gaps_count >= 4
    assert summary.pending_recommendations_count >= 4
    assert summary.active_detector_versions_count >= 2
    assert summary.highest_priority_gap is not None
