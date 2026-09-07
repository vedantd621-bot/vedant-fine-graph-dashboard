"""
Tests for Enterprise Reporting Center, Cryptographic Snapshots & Formula Injection Protection.
"""
import pytest
from backend.app.reporting.exporter import export_to_csv, sanitize_csv_cell
from backend.app.reporting.models import (
    CreateReportRequest, CreateScheduleRequest, ReportFormat, ReportType, ScheduleFrequency
)
from backend.app.reporting.service import ReportingService


@pytest.fixture
def service():
    return ReportingService()


def test_all_8_report_types_generation(service):
    for rtype in ReportType:
        snap = service.generate_report(
            CreateReportRequest(report_type=rtype, format=ReportFormat.JSON),
            tenant_id="tnt_test",
            created_by="tester",
        )
        assert snap.report_type == rtype
        assert snap.content_hash is not None
        assert len(snap.content_hash) == 64  # Valid SHA-256 digest
        assert snap.tenant_id == "tnt_test"


def test_formula_injection_protection():
    # Dangerous formula prefixes (CWE-1236)
    malicious_inputs = [
        ("=SUM(A1:A10)", "'=SUM(A1:A10)"),
        ("+cmd|' /C calc'!A0", "'+cmd|' /C calc'!A0"),
        ("-1+1", "'-1+1"),
        ("@SUM(B1:B5)", "'@SUM(B1:B5)"),
        ("\tcalc", "'\tcalc"),
        ("\rformat", "'\rformat"),
    ]
    for raw, expected in malicious_inputs:
        assert sanitize_csv_cell(raw) == expected

    # Benign string unchanged
    assert sanitize_csv_cell("Normal Entity Name") == "Normal Entity Name"
    assert sanitize_csv_cell(12345) == "12345"

    # CSV export with formula injection test
    dirty_rows = [
        {"account": "=cmd|' /C calc'!A0", "balance": 1000.0, "note": "@alert"},
        {"account": "+123456", "balance": 500.0, "note": "-execute"},
    ]
    csv_content, chash, count = export_to_csv(dirty_rows)
    assert count == 2
    assert "'=cmd" in csv_content
    assert "'@alert" in csv_content
    assert "'+123456" in csv_content
    assert len(chash) == 64


def test_report_export_json_and_csv(service):
    snap = service.generate_report(
        CreateReportRequest(report_type=ReportType.EXECUTIVE_FRAUD_REPORT, format=ReportFormat.JSON),
        tenant_id="tnt_test",
        created_by="tester",
    )
    # Export JSON
    j_content, j_hash, j_mime, j_file = service.export_snapshot(snap.report_id, "tnt_test", ReportFormat.JSON)
    assert j_mime == "application/json"
    assert len(j_hash) == 64

    # Export CSV
    c_content, c_hash, c_mime, c_file = service.export_snapshot(snap.report_id, "tnt_test", ReportFormat.CSV)
    assert c_mime == "text/csv"
    assert len(c_hash) == 64


def test_report_scheduling_lifecycle(service):
    req = CreateScheduleRequest(
        report_type=ReportType.OPERATIONS_REPORT,
        frequency=ScheduleFrequency.WEEKLY,
        title="Weekly Ops Dossier",
        format=ReportFormat.JSON,
    )
    sch = service.create_schedule(req, tenant_id="tnt_test", created_by="tester")
    assert sch.is_active is True
    assert sch.next_run_at is not None

    schedules = service.list_schedules("tnt_test")
    assert any(s.schedule_id == sch.schedule_id for s in schedules)
