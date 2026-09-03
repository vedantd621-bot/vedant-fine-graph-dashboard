"""
FinGraph Forensic Investigation & Search Endpoints.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import (
    get_detection_engine,
    get_neo4j_client,
    get_risk_engine,
)
from backend.app.models.common import ApiResponse
from backend.app.models.investigation import (
    MoneyTrailPath,
    SearchResults,
)
from backend.app.services.account_service import AccountService
from backend.app.services.alert_service import AlertService
from backend.app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/api/v1/investigation", tags=["Investigation"])


def get_investigation_service(
    client=Depends(get_neo4j_client),
    det_eng=Depends(get_detection_engine),
    risk_eng=Depends(get_risk_engine),
) -> InvestigationService:
    acc_svc = AccountService(client=client, risk_engine=risk_eng)
    alt_svc = AlertService(client=client, detection_engine=det_eng, risk_engine=risk_eng)
    return InvestigationService(
        client=client,
        detection_engine=det_eng,
        account_service=acc_svc,
        alert_service=alt_svc,
    )


@router.get("/money-trail", response_model=ApiResponse[List[MoneyTrailPath]])
def trace_money_trail(
    from_account: str = Query(..., description="Starting source account ID"),
    to_account: Optional[str] = Query(None, description="Optional target destination account ID"),
    max_depth: int = Query(4, ge=1, le=6),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    service: InvestigationService = Depends(get_investigation_service),
):
    """Traces multi-hop fund routing paths between financial accounts."""
    paths = service.trace_money_trail(
        from_account=from_account,
        to_account=to_account,
        max_depth=max_depth,
        start_time=start_time,
        end_time=end_time,
    )
    return ApiResponse(data=paths)


@router.get("/search", response_model=ApiResponse[SearchResults])
def search_entities(
    q: str = Query(..., min_length=1, description="Search term for accounts, transactions, or alerts"),
    service: InvestigationService = Depends(get_investigation_service),
):
    """Cross-entity search returning matching accounts, alerts, and transaction IDs."""
    results = service.search_entities(query=q)
    return ApiResponse(data=results)


@router.get("/detections/{detection_id}", response_model=ApiResponse[Dict[str, Any]])
def get_detection_evidence(
    detection_id: str,
    service: InvestigationService = Depends(get_investigation_service),
):
    """Retrieves raw explainable detection object by ID."""
    det = service.get_detection_evidence(detection_id=detection_id)
    if not det:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DETECTION_NOT_FOUND", "message": f"Detection '{detection_id}' was not found."},
        )
    return ApiResponse(data=det)
