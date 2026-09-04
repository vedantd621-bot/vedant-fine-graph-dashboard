"""
FinGraph Forensic Investigation Endpoints.
Multi-hop money trail tracer, cross-entity search, and raw detection evidence inspector.
Protected by Authentication and RBAC.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_investigation_service
from backend.app.models.investigation import (
    DetectionEvidenceResponse,
    MoneyTrailResponse,
    SearchResultItem,
)
from backend.app.security.dependencies import require_analyst, require_investigator
from backend.app.security.models import User
from backend.app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/api/v1/investigation", tags=["Forensic Investigation"])


@router.get("/money-trail", response_model=MoneyTrailResponse)
def trace_money_trail(
    source_account: Optional[str] = Query(None, description="Originating source account ID"),
    destination_account: Optional[str] = Query(None, description="Target destination account ID"),
    from_account: Optional[str] = Query(None, description="Alias for source_account"),
    to_account: Optional[str] = Query(None, description="Alias for destination_account"),
    max_hops: int = Query(4, ge=1, le=6, description="Maximum path hops to traverse"),
    min_amount: Optional[float] = Query(None, ge=0.0, description="Minimum individual hop amount filter"),
    current_user: User = Depends(require_analyst),
    service: InvestigationService = Depends(get_investigation_service),
):
    """Traces multi-hop flow paths between two accounts."""
    src = source_account or from_account
    dst = destination_account or to_account
    if not src or not dst:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MISSING_ACCOUNTS", "message": "Both source_account (from_account) and destination_account (to_account) are required."},
        )

    paths = service.trace_money_trail(
        from_account=src,
        to_account=dst,
        max_depth=max_hops,
    )
    return MoneyTrailResponse(
        source_account=src,
        destination_account=dst,
        paths_found_count=len(paths),
        paths=paths,
        data=paths,
    )


@router.get("/search")
def search_entities(
    q: str = Query(..., min_length=1, description="Search term (account ID, person name, bank, alert, transaction)"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    current_user: User = Depends(require_analyst),
    service: InvestigationService = Depends(get_investigation_service),
):
    """Performs cross-entity search across accounts, persons, banks, transactions, and alerts."""
    results = service.search_entities(query=q)
    return {
        "query": q,
        "data": results.model_dump(mode="json"),
        "accounts": results.accounts,
        "alerts": results.alerts,
        "transaction_ids": results.transaction_ids,
    }


@router.get("/detections/{fingerprint}", response_model=DetectionEvidenceResponse)
def get_detection_by_fingerprint(
    fingerprint: str,
    current_user: User = Depends(require_analyst),
    service: InvestigationService = Depends(get_investigation_service),
):
    """Retrieves raw detection evidence structure for a specific detection fingerprint."""
    det = service.get_detection_evidence(fingerprint)
    if not det:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DETECTION_NOT_FOUND", "message": f"Detection fingerprint '{fingerprint}' not found."},
        )
    return det
