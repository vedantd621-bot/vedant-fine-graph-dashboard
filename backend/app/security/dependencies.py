"""
FinGraph Authentication & RBAC FastAPI Dependencies.
"""
from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.security.jwt import decode_access_token
from backend.app.security.models import Role, User
from backend.app.security.user_store import UserStore, get_user_store

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    user_store: UserStore = Depends(get_user_store),
) -> User:
    """Extracts and verifies JWT token from Authorization Bearer header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_REQUIRED", "message": "Missing or invalid bearer token."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = decode_access_token(credentials.credentials)
    if not claims or "sub" not in claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token is invalid or expired."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_store.get_user_by_id(claims["sub"])
    if not user:
        # Fallback by username
        user = user_store.get_user_by_username(claims.get("username", ""))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_INACTIVE_OR_NOT_FOUND", "message": "User account not active or not found."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_user(
    request: Request,
    token: Optional[str] = Query(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    user_store: UserStore = Depends(get_user_store),
) -> Optional[User]:
    """Extracts user from header or query param without throwing an error if missing."""
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token
    elif "authorization" in request.headers:
        auth_hdr = request.headers["authorization"]
        if auth_hdr.lower().startswith("bearer "):
            raw_token = auth_hdr[7:].strip()

    if not raw_token:
        return None

    claims = decode_access_token(raw_token)
    if not claims or "sub" not in claims:
        return None

    user = user_store.get_user_by_id(claims["sub"])
    if not user:
        user = user_store.get_user_by_username(claims.get("username", ""))

    if user and user.is_active:
        return user
    return None


def require_role(allowed_roles: List[Role]) -> Callable:
    """Dependency factory restricting route access to specified roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": f"Insufficient permissions. Required one of: {[r.value for r in allowed_roles]}",
                },
            )
        return current_user

    return role_checker


# Convenience role dependencies
require_analyst = require_role([Role.ANALYST, Role.INVESTIGATOR, Role.ADMIN])
require_investigator = require_role([Role.INVESTIGATOR, Role.ADMIN])
require_admin = require_role([Role.ADMIN])
