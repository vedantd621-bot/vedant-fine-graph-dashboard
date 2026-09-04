"""
FinGraph Security Headers Middleware.
Applies HTTP hardening headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.config import get_api_config


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects standard enterprise security headers into all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        cfg = get_api_config()
        response = await call_next(request)

        if cfg.security_headers_enabled:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

            # Content Security Policy allows self, API, and local Vite dev assets
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss: http: https:; "
                "font-src 'self' data:;"
            )

            # Strict Transport Security in production HTTPS
            if cfg.app_env.lower() == "production" and cfg.hsts_enabled:
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response
