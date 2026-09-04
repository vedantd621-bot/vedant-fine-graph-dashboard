"""
FinGraph Early Warning Domain Exceptions.
"""

class EarlyWarningError(Exception):
    """Base exception for early warning system."""
    pass


class WarningNotFoundError(EarlyWarningError):
    """Raised when an early warning cannot be found."""
    pass


class InvalidWarningActionError(EarlyWarningError):
    """Raised when an invalid action is performed on an early warning."""
    pass
