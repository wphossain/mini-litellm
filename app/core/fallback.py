"""Multi-provider fallback chain engine."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from app.config.settings import get_config, get_provider_by_name

logger = logging.getLogger(__name__)


async def execute_with_fallback(
    request_func: Callable[[str], Awaitable[Any]],
    initial_provider: str | None = None,
) -> tuple[Any, str]:
    """
    Execute a request with automatic provider fallback.

    Tries each provider in the configured fallback chain in order.
    If initial_provider is set, it's tried first before the chain.

    Args:
        request_func: Async function that takes provider_name and returns a result.
        initial_provider: Optional provider to try before the fallback chain.

    Returns:
        Tuple of (result, provider_name_used).

    Raises:
        RuntimeError: If all providers in the chain fail.
    """
    config = get_config()

    if not config.fallback.enabled:
        if initial_provider:
            result = await request_func(initial_provider)
            return result, initial_provider
        raise RuntimeError("No provider specified and fallback is disabled")

    fallback_chain: list[str] = list(config.fallback.chain)

    # Build ordered list: first the initial provider, then the fallback chain
    ordered_providers: list[str] = []
    seen: set[str] = set()

    if initial_provider:
        ordered_providers.append(initial_provider)
        seen.add(initial_provider)

    for provider_name in fallback_chain:
        if provider_name not in seen:
            ordered_providers.append(provider_name)
            seen.add(provider_name)

    last_error: Exception | None = None

    for provider_name in ordered_providers:
        provider = get_provider_by_name(provider_name)
        if provider is None or not provider.enabled:
            logger.debug("Skipping provider '%s' (not found or disabled)", provider_name)
            continue

        try:
            logger.info("Trying provider '%s'...", provider_name)
            result = await request_func(provider_name)
            logger.info("Provider '%s' succeeded", provider_name)
            return result, provider_name
        except Exception as e:
            last_error = e
            logger.warning("Provider '%s' failed: %s", provider_name, str(e)[:120])
            continue

    raise RuntimeError(
        f"All {len(ordered_providers)} providers in the fallback chain failed. "
        f"Last error: {last_error}"
    )
