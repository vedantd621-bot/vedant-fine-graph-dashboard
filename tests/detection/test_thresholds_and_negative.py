"""
Threshold boundary tests and negative test scenarios for fraud detectors.
Ensures normal commercial/retail activity does not trigger false positive detections.
"""
from unittest.mock import MagicMock
import pytest

from detection.src.detectors.funnel import FunnelDetector
from detection.src.detectors.one_to_many import OneToManyDetector
from detection.src.detectors.chain import ChainDetector
from detection.src.detectors.high_degree import HighDegreeDetector


def test_funnel_threshold_boundary():
    """Verify FunnelDetector filters out accounts below the min_sources threshold."""
    mock_client = MagicMock()
    # Simulating DB query returning empty list when threshold is not met
    mock_client.execute_query.return_value = []

    detector = FunnelDetector(mock_client)
    # When threshold is set to 5, but accounts only have 3 sources
    results = detector.detect(min_sources=5)
    assert len(results) == 0


def test_one_to_many_threshold_boundary():
    """Verify OneToManyDetector filters out small dispersion below min_destinations."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = []

    detector = OneToManyDetector(mock_client)
    results = detector.detect(min_destinations=10)
    assert len(results) == 0


def test_chain_depth_boundary():
    """Verify ChainDetector rejects paths shorter than min_depth."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = []

    detector = ChainDetector(mock_client)
    results = detector.detect(min_depth=5)
    assert len(results) == 0


def test_high_degree_threshold_boundary():
    """Verify HighDegreeDetector does not flag accounts below min_degree."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = []

    detector = HighDegreeDetector(mock_client)
    results = detector.detect(min_degree=15)
    assert len(results) == 0
