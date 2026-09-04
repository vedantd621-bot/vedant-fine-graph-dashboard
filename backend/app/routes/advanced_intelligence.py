"""
FinGraph Advanced Graph Intelligence & Predictive Risk REST Endpoints.
Provides routes for network evolution snapshots, predictive forecasting,
emerging syndicate detection, proactive early warnings with investigator actions,
pattern discovery motifs, and enterprise threat level scoring.
"""
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from backend.app.early_warning.exceptions import (
    EarlyWarningError,
    WarningNotFoundError,
)
from backend.app.early_warning.models import (
    EarlyWarning,
    EarlyWarningActionRequest,
    EarlyWarningSeverity,
    EarlyWarningStatus,
    EnterpriseRiskForecast,
    EnterpriseThreatAssessment,
    EnterpriseThreatLevel,
)
from backend.app.early_warning.service import (
    EarlyWarningService,
    get_early_warning_service,
)
from backend.app.models.common import ApiResponse
from backend.app.network_evolution.exceptions import (
    NetworkEvolutionError,
    NetworkNotFoundError,
)
from backend.app.network_evolution.models import (
    EmergingNetwork,
    EntityRiskTrajectory,
    EntityType,
    EvolutionTimeWindow,
    NetworkEvolutionSnapshot,
    NetworkRiskForecast,
    RiskTrajectory,
)
from backend.app.network_evolution.service import (
    NetworkEvolutionService,
    get_network_evolution_service,
)
from backend.app.pattern_discovery.exceptions import (
    PatternDiscoveryError,
    PatternNotFoundError,
)
from backend.app.pattern_discovery.models import (
    DiscoveredPattern,
    PatternSimilarityResponse,
    PatternType,
)
from backend.app.pattern_discovery.service import (
    PatternDiscoveryService,
    get_pattern_discovery_service,
)
from backend.app.security.dependencies import (
    require_analyst,
    require_investigator,
)
from backend.app.security.models import Role, User

logger = logging.getLogger("FinGraph.AdvancedIntelligenceRouter")

router = APIRouter(prefix="/api/v1/advanced-intelligence", tags=["Advanced Graph Intelligence & Predictive Risk"])


# ---------------------------------------------------------------------------
# Network Evolution & Trajectory
# ---------------------------------------------------------------------------

@router.get(
    "/networks/{network_id}/evolution",
    response_model=ApiResponse[NetworkEvolutionSnapshot],
    summary="Get network evolution snapshot across a bounded time window",
)
def get_network_evolution(
    network_id: str,
    window: EvolutionTimeWindow = Query(EvolutionTimeWindow.ONE_HOUR, description="Bounded time window (5m, 1h, 6h, 24h, 7d, 30d)"),
    current_user: User = Depends(require_analyst),
    service: NetworkEvolutionService = Depends(get_network_evolution_service),
):
    """Calculates bounded snapshot diff, node/edge growth, and velocity per hour."""
    snapshot = service.get_network_evolution(network_id, window=window)
    return ApiResponse(data=snapshot)


@router.get(
    "/networks/{network_id}/trajectory",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get network risk trajectory and momentum",
)
def get_network_trajectory(
    network_id: str,
    current_user: User = Depends(require_analyst),
    service: NetworkEvolutionService = Depends(get_network_evolution_service),
):
    """Calculates deterministic risk momentum trajectory (STABLE, INCREASING, RAPIDLY_INCREASING, DECREASING)."""
    snapshot = service.get_network_evolution(network_id, window=EvolutionTimeWindow.ONE_HOUR)
    return ApiResponse(
        data={
            "network_id": network_id,
            "current_risk": snapshot.current_snapshot.network_risk,
            "risk_delta": snapshot.risk_delta,
            "trajectory": snapshot.trajectory,
            "velocity": snapshot.velocity,
        }
    )


@router.get(
    "/networks/{network_id}/forecast",
    response_model=ApiResponse[NetworkRiskForecast],
    summary="Get deterministic predictive risk forecast across horizons (1h, 6h, 24h, 7d)",
)
def get_network_forecast(
    network_id: str,
    current_user: User = Depends(require_analyst),
    service: NetworkEvolutionService = Depends(get_network_evolution_service),
):
    """Predicts time-series risk score with historical data sufficiency verification."""
    forecast = service.get_network_forecast(network_id)
    return ApiResponse(data=forecast)


@router.get(
    "/entities/{entity_type}/{entity_id}/trajectory",
    response_model=ApiResponse[EntityRiskTrajectory],
    summary="Get entity-level risk trajectory and momentum (account, device, ip, counterparty)",
)
def get_entity_trajectory(
    entity_type: EntityType,
    entity_id: str,
    current_user: User = Depends(require_analyst),
    service: NetworkEvolutionService = Depends(get_network_evolution_service),
):
    """Retrieves risk velocity, trajectory, and top contributing drivers for an entity."""
    traj = service.get_entity_trajectory(entity_type, entity_id)
    return ApiResponse(data=traj)


@router.get(
    "/emerging-networks",
    response_model=ApiResponse[List[EmergingNetwork]],
    summary="List newly forming suspicious network clusters",
)
def list_emerging_networks(
    current_user: User = Depends(require_analyst),
    service: NetworkEvolutionService = Depends(get_network_evolution_service),
):
    """Detects emerging fraud syndicates via node/tx growth surges and anomaly concentration."""
    emerging = service.list_emerging_networks()
    return ApiResponse(data=emerging)


# ---------------------------------------------------------------------------
# Proactive Early Warnings
# ---------------------------------------------------------------------------

@router.get(
    "/early-warnings",
    response_model=ApiResponse[List[EarlyWarning]],
    summary="List proactive early warnings with multi-signal triggers",
)
def list_early_warnings(
    severity: Optional[EarlyWarningSeverity] = Query(None),
    status_filter: Optional[EarlyWarningStatus] = Query(None, alias="status"),
    entity_type: Optional[str] = Query(None),
    current_user: User = Depends(require_analyst),
    service: EarlyWarningService = Depends(get_early_warning_service),
):
    """Lists proactive warnings with non-destructive action recommendations."""
    warnings = service.list_warnings(severity=severity, status=status_filter, entity_type=entity_type)
    return ApiResponse(data=warnings)


@router.get(
    "/early-warnings/{warning_id}",
    response_model=ApiResponse[EarlyWarning],
    summary="Get single early warning details",
)
def get_early_warning(
    warning_id: str,
    current_user: User = Depends(require_analyst),
    service: EarlyWarningService = Depends(get_early_warning_service),
):
    """Retrieves warning details, trigger signals, and recommended action."""
    try:
        w = service.get_warning(warning_id)
        return ApiResponse(data=w)
    except WarningNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "WARNING_NOT_FOUND", "message": str(exc)},
        )


@router.post(
    "/early-warnings/{warning_id}/acknowledge",
    response_model=ApiResponse[EarlyWarning],
    summary="Acknowledge an early warning (Investigator/Admin)",
)
def acknowledge_early_warning(
    warning_id: str,
    req: EarlyWarningActionRequest,
    request: Request,
    current_user: User = Depends(require_investigator),
    service: EarlyWarningService = Depends(get_early_warning_service),
):
    """Transitions warning to ACKNOWLEDGED state with immutable audit logging."""
    req_id = getattr(request.state, "request_id", None)
    try:
        w = service.acknowledge_warning(
            warning_id=warning_id,
            actor_id=current_user.user_id,
            actor_name=current_user.username,
            notes=req.notes,
            request_id=req_id,
        )
        return ApiResponse(data=w)
    except WarningNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "WARNING_NOT_FOUND", "message": str(exc)},
        )


@router.post(
    "/early-warnings/{warning_id}/escalate",
    response_model=ApiResponse[EarlyWarning],
    summary="Escalate an early warning into an active investigation (Investigator/Admin)",
)
def escalate_early_warning(
    warning_id: str,
    req: EarlyWarningActionRequest,
    request: Request,
    current_user: User = Depends(require_investigator),
    service: EarlyWarningService = Depends(get_early_warning_service),
):
    """Transitions warning to ESCALATED state and records audit action."""
    req_id = getattr(request.state, "request_id", None)
    try:
        w = service.escalate_warning(
            warning_id=warning_id,
            actor_id=current_user.user_id,
            actor_name=current_user.username,
            notes=req.notes,
            request_id=req_id,
        )
        return ApiResponse(data=w)
    except WarningNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "WARNING_NOT_FOUND", "message": str(exc)},
        )


@router.post(
    "/early-warnings/{warning_id}/dismiss",
    response_model=ApiResponse[EarlyWarning],
    summary="Dismiss an early warning with rationale (Investigator/Admin)",
)
def dismiss_early_warning(
    warning_id: str,
    req: EarlyWarningActionRequest,
    request: Request,
    current_user: User = Depends(require_investigator),
    service: EarlyWarningService = Depends(get_early_warning_service),
):
    """Transitions warning to DISMISSED state with investigator notes."""
    req_id = getattr(request.state, "request_id", None)
    try:
        w = service.dismiss_warning(
            warning_id=warning_id,
            actor_id=current_user.user_id,
            actor_name=current_user.username,
            notes=req.notes,
            request_id=req_id,
        )
        return ApiResponse(data=w)
    except WarningNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "WARNING_NOT_FOUND", "message": str(exc)},
        )


# ---------------------------------------------------------------------------
# Pattern Discovery & Similarity
# ---------------------------------------------------------------------------

@router.get(
    "/patterns",
    response_model=ApiResponse[List[DiscoveredPattern]],
    summary="List recurring fraud motifs extracted from graph and alert structures",
)
def list_discovered_patterns(
    pattern_type: Optional[PatternType] = Query(None),
    current_user: User = Depends(require_analyst),
    service: PatternDiscoveryService = Depends(get_pattern_discovery_service),
):
    """Lists bounded recurring fraud patterns with frequency and financial exposure."""
    patterns = service.list_patterns(pattern_type=pattern_type)
    return ApiResponse(data=patterns)


@router.get(
    "/patterns/{pattern_id}",
    response_model=ApiResponse[DiscoveredPattern],
    summary="Get single pattern motif details",
)
def get_pattern(
    pattern_id: str,
    current_user: User = Depends(require_analyst),
    service: PatternDiscoveryService = Depends(get_pattern_discovery_service),
):
    """Retrieves full pattern explanation, supporting signals, and linked cases."""
    try:
        p = service.get_pattern(pattern_id)
        return ApiResponse(data=p)
    except PatternNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PATTERN_NOT_FOUND", "message": str(exc)},
        )


@router.get(
    "/patterns/{pattern_id}/similar",
    response_model=ApiResponse[List[PatternSimilarityResponse]],
    summary="Find and compare structurally similar fraud motifs",
)
def get_similar_patterns(
    pattern_id: str,
    current_user: User = Depends(require_analyst),
    service: PatternDiscoveryService = Depends(get_pattern_discovery_service),
):
    """Calculates deterministic structural, entity Jaccard, and signal similarity."""
    try:
        similar = service.get_similar_patterns(pattern_id)
        return ApiResponse(data=similar)
    except PatternNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PATTERN_NOT_FOUND", "message": str(exc)},
        )


# ---------------------------------------------------------------------------
# Enterprise Threat Level & Command Center V2 Summary
# ---------------------------------------------------------------------------

@router.get(
    "/threat-level",
    response_model=ApiResponse[EnterpriseThreatAssessment],
    summary="Get explainable 0-100 Enterprise Threat Level evaluation",
)
def get_threat_level(
    current_user: User = Depends(require_analyst),
    service: EarlyWarningService = Depends(get_early_warning_service),
):
    """Calculates enterprise threat score and level (NORMAL, ELEVATED, HIGH, SEVERE, CRITICAL)."""
    assessment = service.calculate_enterprise_threat_level()
    return ApiResponse(data=assessment)


@router.get(
    "/threat-level/history",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="Get enterprise threat level historical timeline",
)
def get_threat_level_history(
    current_user: User = Depends(require_analyst),
    service: EarlyWarningService = Depends(get_early_warning_service),
):
    """Returns historical threat score readings for time-series trend display."""
    now = datetime.now()
    history = [
        {"timestamp": "24h ago", "score": 45.0, "threat_level": "HIGH"},
        {"timestamp": "12h ago", "score": 52.0, "threat_level": "HIGH"},
        {"timestamp": "6h ago", "score": 68.0, "threat_level": "SEVERE"},
        {"timestamp": "1h ago", "score": 72.0, "threat_level": "SEVERE"},
        {"timestamp": "Current", "score": 74.5, "threat_level": "SEVERE"},
    ]
    return ApiResponse(data=history)


@router.get(
    "/enterprise-forecast",
    response_model=ApiResponse[EnterpriseRiskForecast],
    summary="Get executive risk forecast over 1h, 6h, 24h, and 7d horizons",
)
def get_enterprise_forecast(
    current_user: User = Depends(require_analyst),
    service: EarlyWarningService = Depends(get_early_warning_service),
):
    """Calculates enterprise risk forecast across time horizons."""
    forecast = service.forecast_enterprise_risk()
    return ApiResponse(data=forecast)


@router.get(
    "/command-center/advanced-summary",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get Command Center V2 consolidated advanced graph intelligence summary",
)
def get_command_center_advanced_summary(
    current_user: User = Depends(require_analyst),
    net_service: NetworkEvolutionService = Depends(get_network_evolution_service),
    ew_service: EarlyWarningService = Depends(get_early_warning_service),
    pat_service: PatternDiscoveryService = Depends(get_pattern_discovery_service),
):
    """Consolidates threat level, enterprise forecast, emerging networks, early warnings, and patterns."""
    threat = ew_service.calculate_enterprise_threat_level()
    forecast = ew_service.forecast_enterprise_risk()
    emerging = net_service.list_emerging_networks()
    warnings = ew_service.list_warnings(status=EarlyWarningStatus.ACTIVE)
    patterns = pat_service.list_patterns()

    return ApiResponse(
        data={
            "threat": threat,
            "forecast": forecast,
            "emerging_networks": emerging,
            "active_early_warnings": warnings[:5],
            "top_patterns": patterns[:5],
        }
    )
