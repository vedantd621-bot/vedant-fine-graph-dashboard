"""
FinGraph Authentication Endpoints.
Provides user login, JWT issuance, and authenticated identity retrieval.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.config import get_api_config
from backend.app.security.audit import AuditService, get_audit_service
from backend.app.security.dependencies import get_current_user
from backend.app.security.jwt import create_access_token
from backend.app.security.models import (
    LoginRequest,
    LoginResponse,
    User,
    UserResponse,
)
from backend.app.security.user_store import UserStore, get_user_store

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(
    credentials: LoginRequest,
    user_store: UserStore = Depends(get_user_store),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Authenticates username and password, issuing an RFC 7519 JWT bearer access token."""
    user = user_store.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username or password."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    cfg = get_api_config()
    token_delta = timedelta(minutes=cfg.jwt_access_token_minutes)
    token_claims = {
        "sub": user.user_id,
        "username": user.username,
        "role": user.role.value,
    }
    access_token = create_access_token(token_claims, expires_delta=token_delta)

    # Record login in audit trail
    audit_service.record(
        user_id=user.user_id,
        username=user.username,
        action="USER_LOGIN",
        resource_type="USER",
        resource_id=user.user_id,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=cfg.jwt_access_token_minutes * 60,
        user=UserResponse(
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieves profile and permissions of the currently authenticated user."""
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
