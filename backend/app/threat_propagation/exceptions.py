"""
FinGraph Threat Propagation Exceptions.
"""

class ThreatPropagationError(Exception):
    """Base exception for threat propagation modeling."""
    pass


class OriginEntityNotFoundError(ThreatPropagationError):
    """Raised when an origin entity for propagation analysis does not exist."""
    pass


class InvalidPropagationParamsError(ThreatPropagationError):
    """Raised when propagation parameters are outside acceptable bounds."""
    pass
