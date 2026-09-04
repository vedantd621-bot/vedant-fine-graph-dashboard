"""
FinGraph Autonomous Fraud Intelligence Data Models.
Provides deterministic data structures for detection gaps, adaptive detector recommendations,
human review lifecycles, and detector version registries.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class RecommendationStatus(str, Enum):
    """Lifecycle states for adaptive detection recommendations."""
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPLOYED = "DEPLOYED"


class RecommendationType(str, Enum):
    """Categorization of detection enhancement recommendations."""
    THRESHOLD_TUNE = "THRESHOLD_TUNE"
    NEW_RULE = "NEW_RULE"
    RULE_SUPPRESSION = "RULE_SUPPRESSION"
    WEIGHT_ADJUSTMENT = "WEIGHT_ADJUSTMENT"
    FEATURE_ENHANCEMENT = "FEATURE_ENHANCEMENT"


class EmergingPatternType(str, Enum):
    """Structural motif or behavioral pattern identified in gap analysis."""
    STRUCTURAL_CYCLE = "STRUCTURAL_CYCLE"
    VELOCITY_BURST = "VELOCITY_BURST"
    CENTRALITY_SPIKE = "CENTRALITY_SPIKE"
    DENSE_COMMUNITY = "DENSE_COMMUNITY"
    CROSS_CAMPAIGN = "CROSS_CAMPAIGN"
    UNTRACKED_PROXY_HOP = "UNTRACKED_PROXY_HOP"


class GapPriority(str, Enum):
    """Priority ranking for uncovered detection gaps."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VersionStatus(str, Enum):
    """Deployment status of detector versions."""
    ACTIVE = "ACTIVE"
    SHADOW = "SHADOW"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class DetectionGap(BaseModel):
    """Uncovered structural motif or behavioral blindspot discovered in graph telemetry."""
    gap_id: str = Field(default_factory=lambda: f"gap_{uuid.uuid4().hex[:10]}")
    pattern_type: EmergingPatternType
    title: str
    description: str
    uncovered_motif_count: int = Field(ge=0)
    affected_entities: List[str] = Field(default_factory=list)
    estimated_financial_exposure: float = Field(default=0.0, ge=0.0)
    priority: GapPriority = GapPriority.MEDIUM
    sample_motifs: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = Field(default="OPEN")
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusHistoryEntry(BaseModel):
    """Audit trail record for recommendation state changes."""
    from_status: str
    to_status: str
    transitioned_by: str
    transitioned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None


class DetectorRecommendation(BaseModel):
    """Deterministic proposal to tune, add, or adjust fraud detectors with human-in-the-loop gate."""
    recommendation_id: str = Field(default_factory=lambda: f"rec_{uuid.uuid4().hex[:10]}")
    recommendation_type: RecommendationType
    title: str
    description: str
    target_detector_id: Optional[str] = None
    gap_id: Optional[str] = None
    suggested_parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_impact_summary: str
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)
    status: RecommendationStatus = RecommendationStatus.PROPOSED
    created_by: str = Field(default="autonomous_engine")
    reviewed_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    status_history: List[StatusHistoryEntry] = Field(default_factory=list)
    evidence_notes: Optional[str] = None


class DetectorVersion(BaseModel):
    """Immutable versioned configuration for a fraud detector in production or shadow mode."""
    version_id: str = Field(default_factory=lambda: f"ver_{uuid.uuid4().hex[:10]}")
    detector_id: str
    version_number: str
    parameters: Dict[str, Any]
    status: VersionStatus = VersionStatus.ACTIVE
    created_by: str
    change_rationale: str
    recommendation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecommendationReviewRequest(BaseModel):
    """Payload for reviewing, approving, rejecting, or deploying a detector recommendation."""
    status: RecommendationStatus
    notes: Optional[str] = None
    override_parameters: Optional[Dict[str, Any]] = None


class AutonomousIntelligenceSummary(BaseModel):
    """Dashboard aggregation for autonomous fraud intelligence overview."""
    active_gaps_count: int
    pending_recommendations_count: int
    approved_recommendations_count: int
    active_detector_versions_count: int
    highest_priority_gap: Optional[DetectionGap] = None
    recent_recommendations: List[DetectorRecommendation] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
