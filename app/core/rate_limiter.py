"""Token bucket rate limiter for request throttling."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request, status

from app.config.settings import get_config


class TokenBucket:
    """A simple token bucket rate limiter."""

    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()

    def consume(self, amount: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_refill = now

        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class RateLimiter:
    """Per-key rate limiter using token buckets."""

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}

    def _get_bucket(self, key: str) -> TokenBucket:
        if key not in self._buckets:
            config = get_config()
            rate = config.rate_limiting.requests_per_minute / 60.0
            burst = config.rate_limiting.burst_size
            self._buckets[key] = TokenBucket(rate, burst)
        return self._buckets[key]

    def is_allowed(self, key: str) -> bool:
        """Check if a key is allowed to make a request."""
        bucket = self._get_bucket(key)
        return bucket.consume()

    def cleanup(self, max_age_seconds: int = 3600) -> int:
        """Remove stale buckets to free memory."""
        now = time.monotonic()
        stale = [k for k, b in self._buckets.items()
                  if (now - b.last_refill) > max_age_seconds]
        for k in stale:
            del self._buckets[k]
        return len(stale)


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request) -> None:
    """
    FastAPI dependency — enforces rate limiting.

    Raises 429 if the limit is exceeded.
    """
    config = get_config()

    if not config.rate_limiting.enabled:
        return

    # Use client IP + auth key as the rate limit key
    client_ip = request.client.host if request.client else "unknown"
    auth_header = request.headers.get("Authorization", "")
    limiter_key = f"{client_ip}:{auth_header}"

    if not rate_limiter.is_allowed(limiter_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(config.rate_limiting.requests_per_minute),
            },
        )
