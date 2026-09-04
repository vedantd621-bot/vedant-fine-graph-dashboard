"""
FinGraph Pattern Discovery Domain Exceptions.
"""

class PatternDiscoveryError(Exception):
    """Base exception for pattern discovery."""
    pass


class PatternNotFoundError(PatternDiscoveryError):
    """Raised when a specified pattern motif cannot be found."""
    pass
