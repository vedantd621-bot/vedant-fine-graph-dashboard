"""
FinGraph Shadow Detector Simulation Exceptions.
"""

class ShadowDetectionError(Exception):
    """Base exception for shadow detector simulation operations."""
    pass


class SimulationNotFoundError(ShadowDetectionError):
    """Raised when a specified simulation run is not found."""
    pass


class SimulationExecutionError(ShadowDetectionError):
    """Raised when execution of shadow simulation fails."""
    pass
