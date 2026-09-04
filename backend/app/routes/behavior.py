"""
FinGraph Behavioral Anomaly and Entity Similarity API Endpoints.
Exposes entity baseline profile, temporal multi-window anomaly deviations (5m, 1h, 24h, 7d, 30d),
and explainable multi-factor entity similarity calculations.
Protected by Authentication and RBAC.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_behavior_anomaly_service
from backend.app.models.behavior import (
    EntityBehaviorBaseline,
    EntityBehaviorResponse,
    EntitySimilarityResponse,
    TemporalWindow,
)
from backend.app.security.dependencies import require_analyst
from backend.app.security.models import User
from backend.app.services.behavior_anomaly_service import BehaviorAnomalyService

logger = logging.getLogger("FinGraph.BehaviorRoute")

router = APIRouter(prefix="/api/v1/entities", tags=["Behavioral Anomaly and Similarity"])


@router.get("/{entity_id}/behavior", response_model=EntityBehaviorResponse)
def get_entity_behavior(
    entity_id: str,
    window: TemporalWindow = Query(TemporalWindow.WINDOW_24H, description="Analysis window (5m, 1h, 24h, 7d, 30d)"),
    current_user: User = Depends(require_analyst),
    service: BehaviorAnomalyService = Depends(get_behavior_anomaly_service),
):
    """
    Retrieves statistical baseline and detected deviations for the requested temporal window.
    Evaluates volume spikes, velocity bursts, counterparty dispersion, and directional anomalies.
    """
    behavior_dossier = service.get_entity_behavior(entity_id=entity_id, window=window)
    return behavior_dossier


@router.get("/{entity_id}/baseline", response_model=EntityBehaviorBaseline)
def get_entity_baseline(
    entity_id: str,
    current_user: User = Depends(require_analyst),
    service: BehaviorAnomalyService = Depends(get_behavior_anomaly_service),
):
    """Retrieves 30-day statistical historical behavioral baseline for an entity."""
    baseline = service.get_entity_baseline(entity_id=entity_id)
    return baseline


@router.get("/{entity_id}/similar", response_model=EntitySimilarityResponse)
def get_similar_entities(
    entity_id: str,
    top_k: int = Query(5, ge=1, le=50, description="Maximum number of similar entities to return"),
    current_user: User = Depends(require_analyst),
    service: BehaviorAnomalyService = Depends(get_behavior_anomaly_service),
):
    """
    Calculates explainable behavioral similarity between target entity and suspect peer entities.
    Factors: Jaccard counterparty overlap (0.40), Community co-membership (0.25),
    Risk score proximity (0.20), Volume profile similarity (0.15).
    """
    return service.get_similar_entities(entity_id=entity_id, top_k=top_k)
