"""
FinGraph Administration Endpoints.
Restricted exclusively to users with the ADMIN role.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.models.common import PaginationMeta
from backend.app.security.audit import AuditService, get_audit_service
from backend.app.security.dependencies import require_admin
from backend.app.security.models import (
    AuditLog,
    CreateUserRequest,
    UpdateUserRequest,
    User,
    UserResponse,
)
from backend.app.security.user_store import UserStore, get_user_store

router = APIRouter(prefix="/api/v1/admin", tags=["Administration"])


@router.get("/users", response_model=List[UserResponse])
def list_users(
    admin: User = Depends(require_admin),
    user_store: UserStore = Depends(get_user_store),
):
    """Lists all registered system users and their RBAC roles."""
    users = user_store.list_users()
    return [
        UserResponse(
            user_id=u.user_id,
            username=u.username,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    req: CreateUserRequest,
    admin: User = Depends(require_admin),
    user_store: UserStore = Depends(get_user_store),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Creates a new user account with specified RBAC role."""
    try:
        new_user = user_store.create_user(req)
        audit_service.record(
            user_id=admin.user_id,
            username=admin.username,
            action="USER_CREATED",
            resource_type="USER",
            resource_id=new_user.user_id,
            new_value=f"role={new_user.role.value},username={new_user.username}",
        )
        return UserResponse(
            user_id=new_user.user_id,
            username=new_user.username,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "USER_CREATION_FAILED", "message": str(exc)},
        )


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    req: UpdateUserRequest,
    admin: User = Depends(require_admin),
    user_store: UserStore = Depends(get_user_store),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Updates an existing user's role or active status."""
    target_user = user_store.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": f"User {user_id} not found."},
        )

    old_role = target_user.role.value
    updated = user_store.update_user(user_id, req)

    audit_service.record(
        user_id=admin.user_id,
        username=admin.username,
        action="USER_UPDATED",
        resource_type="USER",
        resource_id=user_id,
        old_value=f"role={old_role},active={target_user.is_active}",
        new_value=f"role={updated.role.value},active={updated.is_active}",
    )

    return UserResponse(
        user_id=updated.user_id,
        username=updated.username,
        role=updated.role,
        is_active=updated.is_active,
        created_at=updated.created_at,
    )


@router.get("/audit")
def list_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin: User = Depends(require_admin),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Retrieves forensic and administrative audit logs."""
    logs, total = audit_service.list_logs(
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "data": logs,
        "pagination": PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    }
