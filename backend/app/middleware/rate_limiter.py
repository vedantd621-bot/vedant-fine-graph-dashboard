"""
FinGraph In-Memory Rate Limiting Middleware.
Protects sensitive and computationally heavy API endpoints against abusive traffic bursts.
"""
import collections
import time
from typing import DefaultDict, Deque, Optional
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.config import get_api_config


_shared_ip_history: DefaultDict[str, Deque[float]] = collections.defaultdict(collections.deque)
_global_rate_limiter: Optional["RateLimiterMiddleware"] = None


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding-window IP rate limiter."""

    def __init__(self, app):
        super().__init__(app)
        self._ip_history = _shared_ip_history
        global _global_rate_limiter
        _global_rate_limiter = self

    def clear(self):
        """Clears all stored rate limit history."""
        _shared_ip_history.clear()

    async def dispatch(self, request: Request, call_next) -> Response:
        cfg = get_api_config()
        if not cfg.rate_limit_enabled:
            return await call_next(request)

        # Rate limit applies to API paths, skipping metrics, health probes, and documentation schemas
        path = request.url.path
        if (
            path.startswith("/health")
            or path.startswith("/live")
            or path.startswith("/ready")
            or path == "/metrics"
            or path == "/openapi.json"
            or path.startswith("/docs")
            or path.startswith("/redoc")
        ):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window = cfg.rate_limit_window_seconds
        max_requests = cfg.rate_limit_requests

        # Stricter limit for authentication attempts
        if path == "/api/v1/auth/login":
            max_requests = min(20, max_requests)

        history = self._ip_history[client_ip]

        # Evict timestamps older than current sliding window
        while history and history[0] <= now - window:
            history.popleft()

        if len(history) >= max_requests:
            retry_after = int(window - (now - history[0])) + 1
            req_id = getattr(request.state, "request_id", "unknown")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(retry_after)},
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded ({max_requests} requests per {window}s). Retry in {retry_after}s.",
                        "request_id": req_id,
                    }
                },
            )

        history.append(now)
        return await call_next(request)


def reset_rate_limiter():
    """Resets the global rate limiter history (used in tests)."""
    if _global_rate_limiter is not None:
        _global_rate_limiter.clear()
