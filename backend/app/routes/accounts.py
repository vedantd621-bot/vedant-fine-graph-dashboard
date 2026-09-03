"""
FinGraph Account REST Endpoints.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from analytics.src.models import RiskLevel
from backend.app.dependencies import (
    get_neo4j_client,
    get_risk_engine,
)
from backend.app.models.accounts import (
    AccountDetail,
    AccountFreezeRequest,
    AccountFreezeResponse,
    AccountSummary,
    AccountTransactionItem,
)
from backend.app.models.common import ApiResponse, PaginatedResponse, PaginationMeta
from backend.app.services.account_service import AccountService

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


def get_account_service(
    client=Depends(get_neo4j_client),
    risk_eng=Depends(get_risk_engine),
) -> AccountService:
    return AccountService(client=client, risk_engine=risk_eng)


@router.get("", response_model=PaginatedResponse[AccountSummary])
def list_accounts(
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by risk category"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0),
    max_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0),
    search: Optional[str] = Query(None, description="Search by account ID substring"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("risk_score", description="Sort field: risk_score, account_id, total_volume, pagerank"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    service: AccountService = Depends(get_account_service),
):
    """Lists accounts with GDS centrality features, community modularity, and risk scores."""
    items, total = service.list_accounts(
        risk_level=risk_level,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        search=search,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return PaginatedResponse(data=items, pagination=meta)


@router.get("/{account_id}", response_model=ApiResponse[AccountDetail])
def get_account_detail(
    account_id: str,
    service: AccountService = Depends(get_account_service),
):
    """Retrieves full account profile with ownership, GDS features, and explainable risk reasons."""
    detail = service.get_account_by_id(account_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ACCOUNT_NOT_FOUND", "message": f"Account '{account_id}' was not found."},
        )
    return ApiResponse(data=detail)


@router.get("/{account_id}/transactions", response_model=PaginatedResponse[AccountTransactionItem])
def get_account_transactions(
    account_id: str,
    direction: Optional[str] = Query(None, description="Filter direction: INCOMING, OUTGOING"),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    min_amount: Optional[float] = Query(None, ge=0.0),
    max_amount: Optional[float] = Query(None, ge=0.0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AccountService = Depends(get_account_service),
):
    """Retrieves chronologically sorted transaction history for an account."""
    items, total = service.get_account_transactions(
        account_id=account_id,
        direction=direction,
        start_time=start_time,
        end_time=end_time,
        min_amount=min_amount,
        max_amount=max_amount,
        page=page,
        page_size=page_size,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return PaginatedResponse(data=items, pagination=meta)


@router.post("/{account_id}/freeze", response_model=ApiResponse[AccountFreezeResponse])
def freeze_account(
    account_id: str,
    payload: AccountFreezeRequest,
    service: AccountService = Depends(get_account_service),
):
    """Simulates an administrative freeze or unfreeze on an account to contain fraudulent activity."""
    res = service.freeze_account(account_id, freeze=payload.freeze, reason=payload.reason)
    return ApiResponse(data=res)
