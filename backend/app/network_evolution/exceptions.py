"""
FinGraph Network Evolution Domain Exceptions.
"""

class NetworkEvolutionError(Exception):
    """Base exception for all network evolution and trajectory errors."""
    pass


class NetworkNotFoundError(NetworkEvolutionError):
    """Raised when a target network is not found."""
    pass


class InsufficientHistoryError(NetworkEvolutionError):
    """Raised when time-series data points are insufficient for forecasting."""
    pass


class InvalidTimeWindowError(NetworkEvolutionError):
    """Raised when an invalid time window is specified."""
    pass
