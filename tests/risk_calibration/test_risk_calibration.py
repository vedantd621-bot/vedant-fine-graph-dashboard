"""
Unit tests for Risk Score Outcome Calibration and Threshold Recommendations.
"""
import pytest
from backend.app.risk_calibration.calibrator import RiskCalibrator
from backend.app.risk_calibration.service import RiskCalibrationService


def test_risk_calibrator_monotonic_bucket_rates():
    calibrator = RiskCalibrator()
    report = calibrator.generate_calibration_report(window_days=30)

    assert len(report.buckets) == 5
    bucket_ids = [b.bucket_id for b in report.buckets]
    assert bucket_ids == ["0-20", "21-40", "41-60", "61-80", "81-100"]

    # Monotonic confirmation rate increase: lower buckets have low confirmation, high buckets have high confirmation
    rates = [b.confirmation_rate for b in report.buckets]
    for i in range(len(rates) - 1):
        assert rates[i] <= rates[i + 1]

    # FPR in top bucket is low
    assert report.buckets[-1].false_positive_rate < 0.10
    assert report.overall_confirmation_rate > 0.30
    assert len(report.suggested_adjustments) >= 2


def test_risk_calibration_service():
    service = RiskCalibrationService()
    report = service.get_latest_report(window_days=30)
    assert report.evaluation_window_days == 30

    refreshed = service.refresh_calibration(window_days=60, user_id="usr_inv_002")
    assert refreshed.evaluation_window_days == 60
