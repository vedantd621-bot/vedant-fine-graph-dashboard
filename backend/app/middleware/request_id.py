"""
FinGraph Request ID Correlation Middleware.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates X-Request-ID header on all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
