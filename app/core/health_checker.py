"""Automated health check with circuit breaker pattern."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

import httpx

from app.config.settings import get_config, get_enabled_providers
from app.models.stats_models import ProviderHealth

logger = logging.getLogger(__name__)


class HealthChecker:
    """Periodic health monitoring for all providers."""

    def __init__(self):
        self._health: dict[str, ProviderHealth] = {}
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    def get_health(self, provider_name: str) -> ProviderHealth:
        return self._health.get(
            provider_name,
            ProviderHealth(name=provider_name, status="healthy"),
        )

    def get_all_health(self) -> list[ProviderHealth]:
        return list(self._health.values())

    def is_healthy(self, provider_name: str) -> bool:
        h = self._health.get(provider_name)
        if h is None:
            return True
        return h.status in ("healthy", "degraded")

    async def _check_provider(self, provider_name: str, url: str, timeout: int) -> None:
        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                latency_ms = (time.monotonic() - start) * 1000

            status_code = response.status_code

            if status_code == 200:
                self._health[provider_name] = ProviderHealth(
                    name=provider_name,
                    status="healthy",
                    last_check=datetime.now(timezone.utc),
                    consecutive_failures=0,
                    avg_latency_ms=latency_ms,
                )
                return

            if status_code == 429:
                self._record_failure(provider_name, "rate_limited", "Rate limited (429)")
                return

            if status_code in (401, 403):
                self._record_failure(provider_name, "auth_error", f"Auth error ({status_code})")
                return

            if status_code >= 500:
                self._record_failure(provider_name, "server_error", f"Server error ({status_code})")
                return

            self._record_failure(provider_name, "unexpected", f"Unexpected status {status_code}")

        except httpx.TimeoutException:
            self._record_failure(provider_name, "timeout", "Request timed out")
        except httpx.ConnectError:
            self._record_failure(provider_name, "connection_error", "Connection failed")
        except Exception as e:
            self._record_failure(provider_name, "error", str(e))

    def _record_failure(self, provider_name: str, status: str, message: str) -> None:
        current = self._health.get(provider_name)
        failures = (current.consecutive_failures + 1) if current else 1
        config = get_config()

        new_status = "unhealthy" if failures >= config.health_check.consecutive_failures else "degraded"

        self._health[provider_name] = ProviderHealth(
            name=provider_name,
            status=new_status,
            last_check=datetime.now(timezone.utc),
            consecutive_failures=failures,
            error_message=message,
        )

        if failures >= config.health_check.consecutive_failures:
            logger.warning("Provider '%s' marked UNHEALTHY after %d failures: %s", provider_name, failures, message)

    async def _run_loop(self) -> None:
        config = get_config()
        interval = config.health_check.interval_seconds
        timeout = config.health_check.timeout_seconds
        endpoints = config.health_check.endpoints
        recovery_interval = config.health_check.recovery_attempts * interval

        cycle = 0

        while not self._stop_event.is_set():
            cycle += 1
            try:
                for provider_name in endpoints:
                    url = endpoints[provider_name]
                    await self._check_provider(provider_name, url, timeout)

                # Check providers without explicit health endpoints via their api_base
                for provider in get_enabled_providers():
                    if provider.name not in endpoints and provider.api_base:
                        await self._check_provider(provider.name, provider.api_base, timeout)

                # Periodic recovery check for unhealthy providers
                if cycle % config.health_check.recovery_attempts == 0:
                    for name, health in self._health.items():
                        if health.status == "unhealthy" and health.consecutive_failures > 0:
                            self._health[name] = ProviderHealth(
                                name=name,
                                status="degraded",
                                last_check=health.last_check,
                                consecutive_failures=max(0, health.consecutive_failures - 1),
                                error_message=health.error_message,
                            )

            except Exception as e:
                logger.error("Health check cycle failed: %s", e)

            await asyncio.wait_for(self._stop_event.wait(), timeout=interval)

    async def start(self) -> None:
        config = get_config()
        if not config.health_check.enabled:
            return
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Health checker started (%ds interval)", config.health_check.interval_seconds)

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health checker stopped")


health_checker = HealthChecker()
