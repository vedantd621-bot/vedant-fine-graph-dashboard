"""
Unit tests for categorical Risk Level boundary thresholds (LOW / MEDIUM / HIGH / CRITICAL).
"""
import pytest
from unittest.mock import MagicMock

from analytics.src.config import RiskScoringConfig
from analytics.src.models import RiskLevel
from analytics.src.risk_engine import ExplainableRiskEngine


def test_risk_level_boundaries():
    """Verify exact boundary mapping of scores to categorical RiskLevel."""
    mock_client = MagicMock()
    config = RiskScoringConfig(
        low_max_score=24.99,
        medium_max_score=49.99,
        high_max_score=74.99,
    )
    engine = ExplainableRiskEngine(client=mock_client, config=config)

    # 1. LOW Risk Band: [0.0 - 24.99]
    assert engine.determine_risk_level(0.0) == RiskLevel.LOW
    assert engine.determine_risk_level(15.0) == RiskLevel.LOW
    assert engine.determine_risk_level(24.9) == RiskLevel.LOW

    # 2. MEDIUM Risk Band: [25.0 - 49.99]
    assert engine.determine_risk_level(25.0) == RiskLevel.MEDIUM
    assert engine.determine_risk_level(37.5) == RiskLevel.MEDIUM
    assert engine.determine_risk_level(49.9) == RiskLevel.MEDIUM

    # 3. HIGH Risk Band: [50.0 - 74.99]
    assert engine.determine_risk_level(50.0) == RiskLevel.HIGH
    assert engine.determine_risk_level(65.0) == RiskLevel.HIGH
    assert engine.determine_risk_level(74.9) == RiskLevel.HIGH

    # 4. CRITICAL Risk Band: [75.0 - 100.0]
    assert engine.determine_risk_level(75.0) == RiskLevel.CRITICAL
    assert engine.determine_risk_level(88.4) == RiskLevel.CRITICAL
    assert engine.determine_risk_level(100.0) == RiskLevel.CRITICAL
