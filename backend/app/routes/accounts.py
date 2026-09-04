"""
FinGraph Account API Endpoints.
Provides account catalog listing, detailed dossier with GDS features, transaction history timeline, and simulated freeze actions.
Protected by Authentication and RBAC.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from analytics.src.models import RiskLevel
from backend.app.dependencies import get_account_service
from backend.app.models.accounts import (
    AccountDetail,
    AccountFreezeRequest,
    AccountFreezeResponse,
    AccountListResponse,
    AccountSummary,
    AccountTransactionListResponse,
)
from backend.app.models.common import PaginationMeta
from backend.app.security.audit import AuditService, get_audit_service
from backend.app.security.dependencies import require_analyst, require_investigator
from backend.app.security.models import User
from backend.app.services.account_service import AccountService

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


@router.get("", response_model=AccountListResponse)
def list_accounts(
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by risk level"),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum risk score threshold"),
    max_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Maximum risk score threshold"),
    community_id: Optional[int] = Query(None, description="Filter by Louvain community group ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort: str = Query("risk_score", description="Sort field (risk_score, pagerank, total_degree)"),
    order: str = Query("desc", description="Sort direction (asc, desc)"),
    current_user: User = Depends(require_analyst),
    service: AccountService = Depends(get_account_service),
):
    """Lists accounts with composite risk scoring, GDS features, and pagination."""
    items, total = service.list_accounts(
        risk_level=risk_level,
        min_score=min_score,
        max_score=max_score,
        community_id=community_id,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return AccountListResponse(
        data=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


@router.get("/{account_id}", response_model=AccountDetail)
def get_account_detail(
    account_id: str,
    current_user: User = Depends(require_analyst),
    service: AccountService = Depends(get_account_service),
):
    """Retrieves full account profile, graph centrality metrics, and explainable risk reasons."""
    detail = service.get_account_by_id(account_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ACCOUNT_NOT_FOUND", "message": f"Account '{account_id}' not found."},
        )
    return detail


@router.get("/{account_id}/transactions", response_model=AccountTransactionListResponse)
def get_account_transactions(
    account_id: str,
    direction: Optional[str] = Query("ALL", description="Transaction direction: ALL, INCOMING, OUTGOING"),
    start_time: Optional[datetime] = Query(None, description="ISO timestamp start window"),
    end_time: Optional[datetime] = Query(None, description="ISO timestamp end window"),
    min_amount: Optional[float] = Query(None, ge=0.0, description="Minimum amount threshold"),
    max_amount: Optional[float] = Query(None, ge=0.0, description="Maximum amount threshold"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(require_analyst),
    service: AccountService = Depends(get_account_service),
):
    """Retrieves settled transaction timeline for an account."""
    acc = service.get_account_by_id(account_id)
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ACCOUNT_NOT_FOUND", "message": f"Account '{account_id}' not found."},
        )

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
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return AccountTransactionListResponse(
        data=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


@router.post("/{account_id}/freeze", response_model=AccountFreezeResponse)
def freeze_account(
    account_id: str,
    req: AccountFreezeRequest,
    current_user: User = Depends(require_investigator),
    service: AccountService = Depends(get_account_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Simulates immediate administrative containment freeze on an account (INVESTIGATOR or ADMIN only)."""
    acc = service.get_account_by_id(account_id)
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ACCOUNT_NOT_FOUND", "message": f"Account '{account_id}' not found."},
        )

    res = service.freeze_account(account_id, freeze=req.freeze, reason=req.reason)

    # Record in audit trail
    audit_service.record(
        user_id=current_user.user_id,
        username=current_user.username,
        action="ACCOUNT_FREEZE" if req.freeze else "ACCOUNT_UNFREEZE",
        resource_type="ACCOUNT",
        resource_id=account_id,
        old_value=str(acc.is_frozen),
        new_value=str(req.freeze),
    )

    return res
