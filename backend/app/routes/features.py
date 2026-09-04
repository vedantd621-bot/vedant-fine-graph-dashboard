"""
FinGraph ML-Ready Feature Generation and Export API Endpoints.
Extracts normalized numerical feature vectors (18 features) across graph, transactional,
and investigative signals, and supports batch CSV / JSON export for downstream ML.
Protected by Authentication and RBAC.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from backend.app.dependencies import get_feature_service
from backend.app.models.features import (
    EntityFeatureVector,
    FeatureDefinition,
    FeatureStoreExportRequest,
    FeatureStoreExportResponse,
)
from backend.app.security.dependencies import require_analyst
from backend.app.security.models import User
from backend.app.services.feature_service import FeatureService

logger = logging.getLogger("FinGraph.FeaturesRoute")

router = APIRouter(prefix="/api/v1/features", tags=["ML Feature Store and Generation"])


@router.get("/catalog", response_model=List[FeatureDefinition])
def get_feature_catalog(
    current_user: User = Depends(require_analyst),
    service: FeatureService = Depends(get_feature_service),
):
    """Retrieves metadata definitions for all 18 normalized ML feature signals."""
    return service.get_feature_catalog()


@router.get("/entity/{entity_id}", response_model=EntityFeatureVector)
def get_entity_feature_vector(
    entity_id: str,
    current_user: User = Depends(require_analyst),
    service: FeatureService = Depends(get_feature_service),
):
    """Computes and returns a normalized 18-dimensional feature vector for a specific account."""
    features = service.extract_entity_features(account_id=entity_id)
    if not features:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ENTITY_NOT_FOUND", "message": f"Account '{entity_id}' not found."},
        )
    return features


@router.post("/export", response_model=FeatureStoreExportResponse)
def export_feature_store(
    request: FeatureStoreExportRequest,
    current_user: User = Depends(require_analyst),
    service: FeatureService = Depends(get_feature_service),
):
    """
    Exports normalized feature vectors for specified accounts (or all active accounts) in CSV or JSON format.
    Suitable for loading directly into scikit-learn, pandas, XGBoost, or Graph Neural Networks.
    """
    export_resp = service.export_features(request=request)
    return export_resp
