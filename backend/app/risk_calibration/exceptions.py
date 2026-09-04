"""
FinGraph Risk Calibration Exceptions.
"""

class RiskCalibrationError(Exception):
    """Base exception for risk score calibration operations."""
    pass


class BucketNotFoundError(RiskCalibrationError):
    """Raised when a specified score bucket is not found."""
    pass
