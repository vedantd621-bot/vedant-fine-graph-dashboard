"""
FinGraph Autonomous Fraud Intelligence, Adaptive Detection & Threat Propagation REST Endpoints.
Provides routes for detection gaps, adaptive recommendations, human review gates,
shadow detector sandbox simulations, risk score calibration, and multi-hop threat propagation.
"""
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from backend.app.autonomous_intelligence.exceptions import (
    AutonomousIntelligenceError,
    GapNotFoundError,
    InvalidStatusTransitionError,
    RecommendationNotFoundError,
    DetectorVersionNotFoundError,
)
from backend.app.autonomous_intelligence.models import (
    AutonomousIntelligenceSummary,
    DetectionGap,
    DetectorRecommendation,
    DetectorVersion,
    RecommendationReviewRequest,
    RecommendationStatus,
    RecommendationType,
)
from backend.app.autonomous_intelligence.service import (
    AutonomousIntelligenceService,
    get_autonomous_intelligence_service,
)
from backend.app.models.common import ApiResponse
from backend.app.risk_calibration.exceptions import (
    BucketNotFoundError,
    RiskCalibrationError,
)
from backend.app.risk_calibration.models import (
    RiskCalibrationReport,
)
from backend.app.risk_calibration.service import (
    RiskCalibrationService,
    get_risk_calibration_service,
)
from backend.app.security.dependencies import (
    require_admin,
    require_analyst,
    require_investigator,
)
from backend.app.security.models import Role, User
from backend.app.shadow_detection.exceptions import (
    ShadowDetectionError,
    SimulationExecutionError,
    SimulationNotFoundError,
)
from backend.app.shadow_detection.models import (
    ShadowSimulationRequest,
    ShadowSimulationResult,
)
from backend.app.shadow_detection.service import (
    ShadowDetectionService,
    get_shadow_detection_service,
)
from backend.app.threat_propagation.exceptions import (
    InvalidPropagationParamsError,
    OriginEntityNotFoundError,
    ThreatPropagationError,
)
from backend.app.threat_propagation.models import (
    ThreatPropagationAnalysis,
)
from backend.app.threat_propagation.service import (
    ThreatPropagationService,
    get_threat_propagation_service,
)

logger = logging.getLogger("FinGraph.AutonomousIntelligenceRouter")

router = APIRouter(
    prefix="/api/v1/autonomous-intelligence",
    tags=["Autonomous Fraud Intelligence, Adaptive Detection & Threat Propagation"],
)


class ThreatPropagationRequest(BaseModel):
    origin_entity_id: str
    max_hops: int = Field(default=3, ge=1, le=5)
    time_window_hours: int = Field(default=24, ge=1, le=168)


# ---------------------------------------------------------------------------
# Executive Summary & Gap Discovery
# ---------------------------------------------------------------------------

@router.get(
    "/summary",
    response_model=ApiResponse[AutonomousIntelligenceSummary],
    summary="Get autonomous intelligence status summary",
)
def get_summary(
    current_user: User = Depends(require_analyst),
    service: AutonomousIntelligenceService = Depends(get_autonomous_intelligence_service),
):
    """Returns aggregated count of active gaps, pending recommendations, and detector versions."""
    summary = service.get_summary()
    return ApiResponse(data=summary)


@router.get(
    "/gaps",
    response_model=ApiResponse[List[DetectionGap]],
    summary="List active detection gaps across graph telemetry",
)
def list_gaps(
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, CRITICAL)"),
    current_user: User = Depends(require_analyst),
    service: AutonomousIntelligenceService = Depends(get_autonomous_intelligence_service),
):
    """Lists uncovered motifs, unflagged cycles, and behavioral blindspots."""
    gaps = service.list_gaps(priority=priority)
    return ApiResponse(data=gaps)


@router.get(
    "/gaps/{gap_id}",
    response_model=ApiResponse[DetectionGap],
    summary="Get single detection gap details",
)
def get_gap(
    gap_id: str,
    current_user: User = Depends(require_analyst),
    service: AutonomousIntelligenceService = Depends(get_autonomous_intelligence_service),
):
    """Retrieves specific detection gap by ID."""
    try:
        gap = service.get_gap(gap_id)
        return ApiResponse(data=gap)
    except GapNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/gaps/scan",
    response_model=ApiResponse[List[DetectionGap]],
    summary="Trigger on-demand scan for detection gaps",
)
def trigger_gap_scan(
    current_user: User = Depends(require_investigator),
    service: AutonomousIntelligenceService = Depends(get_autonomous_intelligence_service),
):
    """Scans graph motifs and transactions to identify fresh detection gaps."""
    fresh_gaps = service.trigger_gap_scan(user_id=current_user.user_id)
    return ApiResponse(data=fresh_gaps)


# ---------------------------------------------------------------------------
# Adaptive Recommendations & Human Approval Gate
# ---------------------------------------------------------------------------

@router.get(
    "/recommendations",
    response_model=ApiResponse[List[DetectorRecommendation]],
    summary="List adaptive detector recommendations",
)
def list_recommendations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (PROPOSED, UNDER_REVIEW, APPROVED, REJECTED, DEPLOYED)"),
    rec_type: Optional[str] = Query(None, description="Filter by recommendation type"),
    current_user: User = Depends(require_analyst),
    service: AutonomousIntelligenceService = Depends(get_autonomous_intelligence_service),
):
    """Lists proposed and reviewed detection enhancements."""
    recs = service.list_recommendations(status=status_filter, rec_type=rec_type)
    return ApiResponse(data=recs)


@router.get(
    "/recommendations/{recommendation_id}",
    response_model=ApiResponse[DetectorRecommendation],
    summary="Get single recommendation details",
)
def get_recommendation(
    recommendation_id: str,
    current_user: User = Depends(require_analyst),
    service: AutonomousIntelligenceService = Depends(get_autonomous_intelligence_service),
):
    """Retrieves detector recommendation details."""
    try:
        rec = service.get_recommendation(recommendation_id)
        return ApiResponse(data=rec)
    except RecommendationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/recommendations/{recommendation_id}/review",
    response_model=ApiResponse[DetectorRecommendation],
    summary="Review, approve, reject, or deploy an adaptive recommendation",
)
def review_recommendation(
    recommendation_id: str,
    payload: RecommendationReviewRequest,
    current_user: User = Depends(require_investigator),
    service: AutonomousIntelligenceService = Depends(get_autonomous_intelligence_service),
):
    """
    Enforces human-in-the-loop governance:
    - INVESTIGATOR can move to UNDER_REVIEW or REJECTED.
    - ADMIN is required to move to APPROVED or DEPLOYED.
    """
    if payload.status in (RecommendationStatus.APPROVED, RecommendationStatus.DEPLOYED):
        if current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required to approve or deploy detector modifications.",
            )

    try:
        updated_rec = service.review_recommendation(
            recommendation_id=recommendation_id,
            request=payload,
            reviewer_id=current_user.user_id,
        )
        return ApiResponse(data=updated_rec)
    except RecommendationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/detector-versions",
    response_model=ApiResponse[List[DetectorVersion]],
    summary="List immutable detector versions",
)
def list_detector_versions(
    detector_id: Optional[str] = Query(None, description="Filter by detector ID"),
    current_user: User = Depends(require_analyst),
    service: AutonomousIntelligenceService = Depends(get_autonomous_intelligence_service),
):
    """Lists configuration versions for production and shadow detectors."""
    versions = service.list_detector_versions(detector_id=detector_id)
    return ApiResponse(data=versions)


# ---------------------------------------------------------------------------
# Shadow Detector Simulation Sandbox
# ---------------------------------------------------------------------------

@router.post(
    "/shadow/simulate",
    response_model=ApiResponse[ShadowSimulationResult],
    summary="Run non-destructive shadow detector simulation",
)
def run_shadow_simulation(
    payload: ShadowSimulationRequest,
    current_user: User = Depends(require_investigator),
    service: ShadowDetectionService = Depends(get_shadow_detection_service),
):
    """Evaluates candidate detector parameters against historical telemetry without creating alerts."""
    try:
        result = service.run_simulation(payload, user_id=current_user.user_id)
        return ApiResponse(data=result)
    except Exception as e:
        logger.exception("Shadow simulation failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/shadow/simulations",
    response_model=ApiResponse[List[ShadowSimulationResult]],
    summary="List shadow detector simulation runs",
)
def list_shadow_simulations(
    detector_id: Optional[str] = Query(None, description="Filter by detector ID"),
    current_user: User = Depends(require_analyst),
    service: ShadowDetectionService = Depends(get_shadow_detection_service),
):
    """Retrieves history of shadow evaluation runs."""
    sims = service.list_simulations(detector_id=detector_id)
    return ApiResponse(data=sims)


@router.get(
    "/shadow/simulations/{simulation_id}",
    response_model=ApiResponse[ShadowSimulationResult],
    summary="Get single shadow simulation result",
)
def get_shadow_simulation(
    simulation_id: str,
    current_user: User = Depends(require_analyst),
    service: ShadowDetectionService = Depends(get_shadow_detection_service),
):
    """Retrieves specific shadow simulation result."""
    try:
        sim = service.get_simulation(simulation_id)
        return ApiResponse(data=sim)
    except SimulationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Risk Calibration & Threshold Analytics
# ---------------------------------------------------------------------------

@router.get(
    "/risk-calibration",
    response_model=ApiResponse[RiskCalibrationReport],
    summary="Get empirical risk score calibration report",
)
def get_risk_calibration(
    window_days: int = Query(30, ge=7, le=180, description="Evaluation window in days"),
    current_user: User = Depends(require_analyst),
    service: RiskCalibrationService = Depends(get_risk_calibration_service),
):
    """Analyzes 5-bucket risk score performance vs confirmed fraud outcomes."""
    report = service.get_latest_report(window_days=window_days)
    return ApiResponse(data=report)


@router.post(
    "/risk-calibration/refresh",
    response_model=ApiResponse[RiskCalibrationReport],
    summary="Force refresh empirical risk score calibration",
)
def refresh_risk_calibration(
    window_days: int = Query(30, ge=7, le=180, description="Evaluation window in days"),
    current_user: User = Depends(require_investigator),
    service: RiskCalibrationService = Depends(get_risk_calibration_service),
):
    """Recomputes calibration metrics across investigation outcomes."""
    report = service.refresh_calibration(window_days=window_days, user_id=current_user.user_id)
    return ApiResponse(data=report)


# ---------------------------------------------------------------------------
# Multi-Hop Threat Propagation
# ---------------------------------------------------------------------------

@router.post(
    "/threat-propagation/analyze",
    response_model=ApiResponse[ThreatPropagationAnalysis],
    summary="Analyze multi-hop threat propagation from origin entity",
)
def analyze_threat_propagation(
    payload: ThreatPropagationRequest,
    current_user: User = Depends(require_investigator),
    service: ThreatPropagationService = Depends(get_threat_propagation_service),
):
    """Simulates bounded multi-hop contagion spread, computes 6-factor propagation score and topology."""
    try:
        analysis = service.analyze_entity(
            origin_entity_id=payload.origin_entity_id,
            max_hops=payload.max_hops,
            time_window_hours=payload.time_window_hours,
            user_id=current_user.user_id,
        )
        return ApiResponse(data=analysis)
    except OriginEntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception("Threat propagation analysis failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/threat-propagation/entities/{entity_id}",
    response_model=ApiResponse[ThreatPropagationAnalysis],
    summary="Get threat propagation analysis for specific entity",
)
def get_entity_threat_propagation(
    entity_id: str,
    max_hops: int = Query(3, ge=1, le=5),
    time_window_hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(require_analyst),
    service: ThreatPropagationService = Depends(get_threat_propagation_service),
):
    """Retrieves or executes threat propagation modeling for target entity."""
    try:
        analysis = service.analyze_entity(
            origin_entity_id=entity_id,
            max_hops=max_hops,
            time_window_hours=time_window_hours,
            user_id=current_user.user_id,
        )
        return ApiResponse(data=analysis)
    except OriginEntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
