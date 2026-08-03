"""Automatic retry with exponential backoff and jitter."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Awaitable, Callable

from app.config.settings import get_config

logger = logging.getLogger(__name__)


async def retry_with_backoff(
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    max_retries: int | None = None,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retryable_statuses: frozenset[int] | None = None,
    **kwargs: Any,
) -> tuple[Any, int]:
    """
    Execute an async function with exponential backoff retry.
    Retries on HTTP 429, 500, 502, 503, 504 and network errors.
    Returns (result, attempt_count).
    """
    if retryable_statuses is None:
        retryable_statuses = frozenset({429, 500, 502, 503, 504})
    if max_retries is None:
        max_retries = get_config().model_routing.max_retries_per_request

    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            return result, attempt
        except Exception as e:
            last_exception = e
            should_retry = False

            if hasattr(e, "status_code"):
                if getattr(e, "status_code") in retryable_statuses:
                    should_retry = True

            if isinstance(e, (ConnectionError, TimeoutError, asyncio.TimeoutError)):
                should_retry = True

            error_msg = str(e).lower()
            if any(kw in error_msg for kw in ("429", "rate limit", "server error", "503", "502", "timeout", "connection")):
                should_retry = True

            if not should_retry or attempt >= max_retries:
                raise

            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.5)
            total_delay = delay + jitter

            logger.warning("Retry %d/%d after %.1fs: %s", attempt + 1, max_retries, total_delay, str(e)[:120])
            await asyncio.sleep(total_delay)

    raise last_exception or RuntimeError("Retry exhausted")
