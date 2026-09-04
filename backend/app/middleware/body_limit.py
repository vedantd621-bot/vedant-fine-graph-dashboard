"""
FinGraph Request Body Size Limit Middleware.
"""
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.config import get_api_config


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforces upper boundary on incoming HTTP request body sizes."""

    async def dispatch(self, request: Request, call_next) -> Response:
        cfg = get_api_config()
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                length = int(content_length)
                if length > cfg.max_request_body_bytes:
                    req_id = getattr(request.state, "request_id", "unknown")
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Request body exceeds maximum allowed size of {cfg.max_request_body_bytes} bytes.",
                                "request_id": req_id,
                            }
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)
