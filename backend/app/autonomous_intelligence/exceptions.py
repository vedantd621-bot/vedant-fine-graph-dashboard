"""
FinGraph Autonomous Fraud Intelligence Domain Exceptions.
"""

class AutonomousIntelligenceError(Exception):
    """Base exception for autonomous fraud intelligence domain."""
    pass


class GapNotFoundError(AutonomousIntelligenceError):
    """Raised when a specified detection gap is not found."""
    pass


class RecommendationNotFoundError(AutonomousIntelligenceError):
    """Raised when a specified detector recommendation is not found."""
    pass


class InvalidStatusTransitionError(AutonomousIntelligenceError):
    """Raised when an invalid lifecycle status transition is attempted."""
    pass


class DetectorVersionNotFoundError(AutonomousIntelligenceError):
    """Raised when a detector version specification is not found."""
    pass
