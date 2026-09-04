"""
Pytest configuration and global fixtures for FinGraph tests.
"""
import pytest
from backend.app.middleware.rate_limiter import _shared_ip_history, _global_rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Resets rate limiter history between tests to prevent test-suite request starvation."""
    _shared_ip_history.clear()
    if _global_rate_limiter is not None:
        _global_rate_limiter.clear()
    yield
    _shared_ip_history.clear()
    if _global_rate_limiter is not None:
        _global_rate_limiter.clear()
