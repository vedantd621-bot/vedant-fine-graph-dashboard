"""
FinGraph Secure Password Hashing & Verification.
Uses PBKDF2-HMAC-SHA256 with cryptographic salt and 150,000 iterations.
"""
import hashlib
import hmac
import os
import secrets
from typing import Tuple


def hash_password(plain_password: str, iterations: int = 150_000) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a secure 32-byte salt."""
    salt = secrets.token_bytes(32)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${pwd_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hashed password string."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False
        algorithm, iterations_str, salt_hex, hash_hex = parts
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(computed_hash, expected_hash)
    except Exception:
        return False
