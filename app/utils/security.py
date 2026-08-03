"""Security utilities: key masking, hash generation, sanitization."""

from __future__ import annotations

import hashlib
import re
import secrets


def mask_key(key: str, visible: int = 4) -> str:
    """Mask an API key showing only first and last N characters."""
    if not key:
        return "***"
    if len(key) <= visible * 2:
        return "*" * len(key)
    return key[:visible] + "*" * (len(key) - visible * 2) + key[-visible:]


def hash_key(key: str) -> str:
    """SHA-256 hash a key for safe storage/comparison."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key(prefix: str = "sk") -> str:
    """Generate a secure random API key."""
    random_part = secrets.token_hex(24)
    return f"{prefix}-{random_part}"


def validate_key_format(key: str) -> bool:
    """Basic validation that a key looks reasonable (not a secret check)."""
    if not key or len(key) < 8:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_\-.]{8,}$", key))


def sanitize_for_log(value: str | None, max_len: int = 500) -> str:
    """Sanitize a string for safe logging — truncate and strip newlines."""
    if value is None:
        return ""
    cleaned = value.replace("\n", " ").replace("\r", " ").strip()
    if len(cleaned) > max_len:
        return cleaned[:max_len] + "..."
    return cleaned


def redact_sensitive_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return sanitized headers with API keys redacted."""
    sensitive = {"authorization", "x-api-key", "api-key", "x-auth-token"}
    result: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in sensitive:
            result[key] = mask_key(value)
        else:
            result[key] = value
    return result
