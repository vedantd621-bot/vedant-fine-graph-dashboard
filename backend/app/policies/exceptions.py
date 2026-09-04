"""
FinGraph Policy Engine Exceptions.
"""

class PolicyError(Exception):
    """Base exception for policy operations."""
    pass

class PolicyNotFoundError(PolicyError):
    """Raised when a policy ID is not found."""
    pass

class PolicyValidationError(PolicyError):
    """Raised when a policy structure is invalid."""
    pass

class PolicyEvaluationError(PolicyError):
    """Raised when an error occurs during policy evaluation."""
    pass
