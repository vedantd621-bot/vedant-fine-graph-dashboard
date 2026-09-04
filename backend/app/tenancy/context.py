"""
FinGraph Tenant Context Resolution & Request Scoping.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from fastapi import Depends, HTTPException, Request, status

from backend.app.security.dependencies import get_current_user
from backend.app.security.models import Role, User


@dataclass
class TenantContext:
    """Scoped security context for authenticated tenant requests."""
    tenant_id: str
    org_id: Optional[str]
    user_id: str
    username: str
    role: Role
    is_platform_admin: bool = False
    permissions: List[str] = field(default_factory=list)

    def is_in_tenant(self, resource_tenant_id: str) -> bool:
        """Verifies if request has access to the target tenant resource."""
        if self.is_platform_admin:
            return True
        return self.tenant_id == resource_tenant_id


def get_tenant_context(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> TenantContext:
    """
    Extracts server-side verified tenant context from the authenticated user.
    Never trusts conflicting client headers.
    """
    tenant_id = getattr(current_user, "tenant_id", "tnt_default")
    org_id = getattr(current_user, "organization_id", "org_default")
    is_platform_admin = current_user.role == Role.PLATFORM_ADMIN if hasattr(Role, "PLATFORM_ADMIN") else False

    # Optional check: If a tenant header is provided, it must match user's tenant unless user is platform admin
    header_tenant = request.headers.get("X-Tenant-ID")
    if header_tenant and header_tenant != tenant_id and not is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "CROSS_TENANT_ACCESS_DENIED",
                "message": f"Authenticated user is bound to tenant '{tenant_id}' and cannot operate on '{header_tenant}'.",
            },
        )

    # Use header tenant for platform admin if explicitly switching view
    effective_tenant = header_tenant if (is_platform_admin and header_tenant) else tenant_id

    permissions = getattr(current_user, "permissions", [])
    return TenantContext(
        tenant_id=effective_tenant,
        org_id=org_id,
        user_id=current_user.user_id,
        username=current_user.username,
        role=current_user.role,
        is_platform_admin=is_platform_admin,
        permissions=permissions,
    )
