"""API Key authentication with master, admin, and readonly key tiers."""

from __future__ import annotations

import secrets
from typing import Literal

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.settings import get_config

security_scheme = HTTPBearer(auto_error=False)

KeyTier = Literal["master", "admin", "readonly"]


def _constant_time_compare(a: str, b: str) -> bool:
    """Time-constant string comparison to prevent timing attacks."""
    return secrets.compare_digest(a.encode(), b.encode())


def validate_key(token: str | None) -> tuple[bool, KeyTier | None]:
    """
    Validate an API key against configured keys.

    Returns (is_valid, tier).
    """
    if not token:
        return False, None

    config = get_config()

    # Strip 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    # Master key
    if config.auth.master_key and _constant_time_compare(token, config.auth.master_key):
        return True, "master"

    # Admin key
    if config.auth.admin_key and _constant_time_compare(token, config.auth.admin_key):
        return True, "admin"

    # Readonly key
    if config.auth.readonly_key and _constant_time_compare(token, config.auth.readonly_key):
        return True, "readonly"

    return False, None


async def require_auth(request: Request) -> tuple[str, KeyTier]:
    """
    FastAPI dependency — requires a valid API key.

    Returns (token, tier) if valid, raises 401 otherwise.
    """
    config = get_config()

    if config.auth.disabled:
        return "anonymous", "master"

    credentials: HTTPAuthorizationCredentials | None = await security_scheme(request)

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide it as: Bearer YOUR_API_KEY",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    is_valid, tier = validate_key(token)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token, tier


async def require_admin(request: Request) -> str:
    """
    FastAPI dependency — requires admin or master key.

    Returns the token if valid, raises 403 otherwise.
    """
    token, tier = await require_auth(request)

    if tier not in ("master", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or master API key required",
        )

    return token


def mask_key(key: str) -> str:
    """Mask an API key for safe logging."""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]
