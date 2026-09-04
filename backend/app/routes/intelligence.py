"""
FinGraph Advanced Fraud Intelligence Endpoints.
Exposes rich entity risk profiles, ranked explainable risk factors,
chronological event timelines, multi-alert correlation, and investigation analytics.
Protected by Authentication and RBAC.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_intelligence_service
from backend.app.models.intelligence import (
    AlertCorrelation,
    AlertRecommendationsResponse,
    EntityRiskProfile,
    EntityType,
    InvestigationAnalytics,
    InvestigationTimelineResponse,
    RiskExplanationResponse,
)
from backend.app.security.dependencies import require_analyst
from backend.app.security.models import User
from backend.app.services.intelligence_service import IntelligenceService

router = APIRouter(prefix="/api/v1", tags=["Fraud Intelligence & Explainability"])


@router.get("/entities/{entity_id}/risk-profile", response_model=EntityRiskProfile)
def get_entity_risk_profile(
    entity_id: str,
    entity_type: EntityType = Query(EntityType.ACCOUNT, description="Type of entity: ACCOUNT, PERSON"),
    current_user: User = Depends(require_analyst),
    service: IntelligenceService = Depends(get_intelligence_service),
):
    """Retrieves rich multi-dimensional risk profile with graph metrics, detector hits, and history."""
    profile = service.get_entity_risk_profile(entity_id=entity_id, entity_type=entity_type)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ENTITY_NOT_FOUND", "message": f"Entity '{entity_id}' of type '{entity_type.value}' not found."},
        )
    return profile


@router.get("/entities/{entity_id}/risk-explanation", response_model=RiskExplanationResponse)
def get_entity_risk_explanation(
    entity_id: str,
    current_user: User = Depends(require_analyst),
    service: IntelligenceService = Depends(get_intelligence_service),
):
    """Provides explainable breakdown explaining why an account is elevated risk with evidence grounding."""
    explanation = service.get_risk_explanation(entity_id=entity_id)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ENTITY_NOT_FOUND", "message": f"Account '{entity_id}' not found."},
        )
    return explanation


@router.get("/entities/{entity_id}/timeline", response_model=InvestigationTimelineResponse)
def get_entity_investigation_timeline(
    entity_id: str,
    current_user: User = Depends(require_analyst),
    service: IntelligenceService = Depends(get_intelligence_service),
):
    """Retrieves a unified chronological forensic event stream across transactions, detections, alerts, and cases."""
    return service.get_entity_timeline(entity_id=entity_id)


@router.get("/alerts/{alert_id}/correlated", response_model=AlertCorrelation)
def get_correlated_alerts(
    alert_id: str,
    current_user: User = Depends(require_analyst),
    service: IntelligenceService = Depends(get_intelligence_service),
):
    """Discovers correlated alerts sharing counterparties, accounts, or topological syndicate clusters."""
    correlation = service.correlate_alert(alert_id=alert_id)
    if not correlation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert '{alert_id}' not found."},
        )
    return correlation


@router.get("/alerts/{alert_id}/recommendations", response_model=AlertRecommendationsResponse)
def get_alert_recommendations(
    alert_id: str,
    current_user: User = Depends(require_analyst),
    service: IntelligenceService = Depends(get_intelligence_service),
):
    """Generates evidence-backed next-step recommendations for an investigator."""
    recommendations = service.get_alert_recommendations(alert_id=alert_id)
    if not recommendations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert '{alert_id}' not found."},
        )
    return recommendations


@router.get("/investigation/analytics", response_model=InvestigationAnalytics)
def get_investigation_analytics(
    current_user: User = Depends(require_analyst),
    service: IntelligenceService = Depends(get_intelligence_service),
):
    """Aggregates forensic intelligence metrics across active cases, alerts, and high-risk entities."""
    return service.get_investigation_analytics()
