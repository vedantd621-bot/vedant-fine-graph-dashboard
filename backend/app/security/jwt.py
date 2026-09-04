"""
FinGraph JWT Token Generation & Validation.
Implements RFC 7519 standard JSON Web Tokens using HMAC-SHA256 signatures and UTC expiration.
"""
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from backend.app.config import get_api_config


def _base64url_encode(data: bytes) -> str:
    """Encodes bytes to base64url string without padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(data: str) -> bytes:
    """Decodes base64url string with padding restoration."""
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(
    payload: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None,
) -> str:
    """Generates a signed JWT access token with expiration."""
    cfg = get_api_config()
    secret = secret_key or cfg.jwt_secret

    header = {"alg": cfg.jwt_algorithm, "typ": "JWT"}
    now_ts = int(time.time())

    if expires_delta:
        exp_ts = int((datetime.now(timezone.utc) + expires_delta).timestamp())
    else:
        exp_ts = now_ts + (cfg.jwt_access_token_minutes * 60)

    claims = dict(payload)
    claims.setdefault("iat", now_ts)
    claims["exp"] = exp_ts

    header_bytes = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    claims_bytes = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")

    encoded_header = _base64url_encode(header_bytes)
    encoded_claims = _base64url_encode(claims_bytes)

    signing_input = f"{encoded_header}.{encoded_claims}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_signature = _base64url_encode(signature)

    return f"{encoded_header}.{encoded_claims}.{encoded_signature}"


def decode_access_token(
    token: str,
    secret_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Validates signature and expiration of JWT token and returns claims dictionary."""
    cfg = get_api_config()
    secret = secret_key or cfg.jwt_secret

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        encoded_header, encoded_claims, encoded_signature = parts
        signing_input = f"{encoded_header}.{encoded_claims}".encode("utf-8")

        expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _base64url_decode(encoded_signature)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        claims_bytes = _base64url_decode(encoded_claims)
        claims = json.loads(claims_bytes.decode("utf-8"))

        # Expiration check
        exp = claims.get("exp")
        if exp is not None and time.time() > exp:
            return None

        return claims
    except Exception:
        return None
