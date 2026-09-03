"""
Unit tests for Time Window parameterization in fraud detectors.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from detection.src.detectors.funnel import FunnelDetector
from detection.src.detectors.circular import CircularFlowDetector
from detection.src.detectors.one_to_many import OneToManyDetector


def test_time_window_parameter_passing():
    """Verify detectors pass start_time and end_time ISO strings to Neo4j queries."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = []

    start_dt = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 8, 5, 23, 59, 59, tzinfo=timezone.utc)

    # 1. Funnel Detector
    funnel_det = FunnelDetector(mock_client)
    funnel_det.detect(start_time=start_dt, end_time=end_dt)
    mock_client.execute_query.assert_called_once()
    params = mock_client.execute_query.call_args.args[1]
    assert params["start_time"] == "2026-08-01T00:00:00+00:00"
    assert params["end_time"] == "2026-08-05T23:59:59+00:00"

    # 2. Circular Detector
    mock_client.reset_mock()
    circ_det = CircularFlowDetector(mock_client)
    circ_det.detect(start_time=start_dt, end_time=end_dt)
    mock_client.execute_query.assert_called_once()
    params = mock_client.execute_query.call_args.args[1]
    assert params["start_time"] == "2026-08-01T00:00:00+00:00"
    assert params["end_time"] == "2026-08-05T23:59:59+00:00"

    # 3. OneToMany Detector
    mock_client.reset_mock()
    otm_det = OneToManyDetector(mock_client)
    otm_det.detect(start_time=start_dt, end_time=end_dt)
    mock_client.execute_query.assert_called_once()
    params = mock_client.execute_query.call_args.args[1]
    assert params["start_time"] == "2026-08-01T00:00:00+00:00"
    assert params["end_time"] == "2026-08-05T23:59:59+00:00"
