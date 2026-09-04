"""
FinGraph Tenancy & Governance Exceptions.
"""

class TenancyError(Exception):
    """Base exception for all tenancy and control-plane errors."""
    pass

class TenantNotFoundError(TenancyError):
    """Raised when a requested tenant cannot be found."""
    pass

class TenantSuspendedError(TenancyError):
    """Raised when an operation is attempted on a suspended or disabled tenant."""
    pass

class QuotaExceededError(TenancyError):
    """Raised when a tenant operation breaches resource quotas."""
    pass

class CrossTenantAccessError(TenancyError):
    """Raised when an unauthorized cross-tenant resource access is attempted."""
    pass

class InvalidTenantStateTransitionError(TenancyError):
    """Raised when an illegal tenant lifecycle transition is requested."""
    pass

class TeamNotFoundError(TenancyError):
    """Raised when a requested team cannot be found."""
    pass

class OrganizationNotFoundError(TenancyError):
    """Raised when an organization is not found."""
    pass
