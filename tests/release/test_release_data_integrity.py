"""
Release Test: Automated Data Integrity Verification.
"""
import pytest
from scripts.data_integrity_check import run_integrity_audit


def test_data_integrity_audit_passes():
    report = run_integrity_audit()
    assert report.errors == 0, f"Integrity check failed with errors: {report.details}"
    assert report.duplicates == 0
    assert report.missing_risk_scores == 0
    assert report.records_checked > 0
