"""
Unit tests for Analytics CLI execution.
"""
from unittest.mock import MagicMock, patch
import pytest

from analytics.src.cli import main, print_risk_report
from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals


def test_print_risk_report_output(capsys):
    """Verify print_risk_report outputs formatted report."""
    score = RiskScore(
        account_id="A005",
        score=78.5,
        risk_level=RiskLevel.CRITICAL,
        rule_subscore=35.0,
        graph_subscore=70.0,
        features=GraphFeatures(account_id="A005", pagerank=0.55, total_degree=5, total_volume=71280.0),
        rule_signals=RuleSignals(account_id="A005", funnel_flag=True, active_detections_count=1, detection_types=["FUNNEL"]),
        reasons=["Account functions as an intermediary aggregation mule."],
    )

    print_risk_report([score])
    captured = capsys.readouterr()
    assert "FinGraph Account Risk & GDS Analytics Report" in captured.out
    assert "A005" in captured.out
    assert "CRITICAL" in captured.out


def test_cli_dry_run_mode(capsys):
    """Verify CLI dry run execution."""
    with patch("sys.argv", ["cli.py", "--dry-run"]):
        main()
        captured = capsys.readouterr()
        assert "Dry run mode" in captured.out
        assert "SUCCESS" in captured.out
