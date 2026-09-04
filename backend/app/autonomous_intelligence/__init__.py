"""
FinGraph Autonomous Fraud Intelligence Package.
"""
from backend.app.autonomous_intelligence.models import (
    AutonomousIntelligenceSummary,
    DetectionGap,
    DetectorRecommendation,
    DetectorVersion,
    EmergingPatternType,
    GapPriority,
    RecommendationReviewRequest,
    RecommendationStatus,
    RecommendationType,
    VersionStatus,
)
from backend.app.autonomous_intelligence.service import AutonomousIntelligenceService
from backend.app.autonomous_intelligence.exceptions import (
    AutonomousIntelligenceError,
    GapNotFoundError,
    InvalidStatusTransitionError,
    RecommendationNotFoundError,
    DetectorVersionNotFoundError,
)

__all__ = [
    "AutonomousIntelligenceService",
    "DetectionGap",
    "DetectorRecommendation",
    "DetectorVersion",
    "AutonomousIntelligenceSummary",
    "RecommendationReviewRequest",
    "RecommendationStatus",
    "RecommendationType",
    "EmergingPatternType",
    "GapPriority",
    "VersionStatus",
    "AutonomousIntelligenceError",
    "GapNotFoundError",
    "InvalidStatusTransitionError",
    "RecommendationNotFoundError",
    "DetectorVersionNotFoundError",
]
