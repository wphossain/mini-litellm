"""Async request/response logger with in-memory storage and optional disk persistence."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.stats_models import RequestLog


class GatewayLogger:
    """Thread-safe, async logger for gateway requests."""

    def __init__(self, max_entries: int = 10000):
        self._logs: list[RequestLog] = []
        self._lock = asyncio.Lock()
        self._max_entries = max_entries

    async def log_request(
        self,
        method: str,
        path: str,
        model: str | None = None,
        provider: str | None = None,
        status_code: int = 200,
        latency_ms: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
        error: str | None = None,
        client_ip: str | None = None,
        api_key_label: str | None = None,
    ) -> RequestLog:
        entry = RequestLog(
            id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(timezone.utc),
            method=method,
            path=path,
            model=model,
            provider=provider,
            status_code=status_code,
            latency_ms=round(latency_ms, 2),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=round(estimated_cost_usd, 8),
            error=error,
            client_ip=client_ip,
            api_key_label=api_key_label,
        )

        async with self._lock:
            self._logs.append(entry)
            if len(self._logs) > self._max_entries:
                self._logs = self._logs[-self._max_entries:]

        return entry

    async def get_logs(self, limit: int = 100, offset: int = 0) -> tuple[list[RequestLog], int]:
        async with self._lock:
            total = len(self._logs)
            start = max(0, total - offset - limit)
            end = total - offset
            items = list(reversed(self._logs[start:end]))
            return items, total

    async def get_stats(self) -> dict[str, Any]:
        async with self._lock:
            if not self._logs:
                return {
                    "total_requests": 0,
                    "total_errors": 0,
                    "total_tokens": 0,
                    "avg_latency_ms": 0.0,
                    "estimated_cost_usd": 0.0,
                }

            total = len(self._logs)
            errors = sum(1 for l in self._logs if l.error)
            total_tokens = sum(l.total_tokens for l in self._logs)
            avg_latency = sum(l.latency_ms for l in self._logs) / total if total > 0 else 0
            total_cost = sum(l.estimated_cost_usd for l in self._logs)

            # Per-provider breakdown
            by_provider: dict[str, dict[str, Any]] = {}
            for log in self._logs:
                if log.provider:
                    if log.provider not in by_provider:
                        by_provider[log.provider] = {"requests": 0, "errors": 0, "tokens": 0, "cost": 0.0}
                    by_provider[log.provider]["requests"] += 1
                    if log.error:
                        by_provider[log.provider]["errors"] += 1
                    by_provider[log.provider]["tokens"] += log.total_tokens
                    by_provider[log.provider]["cost"] += log.estimated_cost_usd

            return {
                "total_requests": total,
                "total_errors": errors,
                "total_tokens": total_tokens,
                "avg_latency_ms": round(avg_latency, 2),
                "estimated_cost_usd": round(total_cost, 6),
                "by_provider": by_provider,
            }

    async def save_to_file(self, filepath: str) -> None:
        async with self._lock:
            data = [log.model_dump(mode="json") for log in self._logs]
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    async def clear(self) -> None:
        async with self._lock:
            self._logs.clear()


gateway_logger = GatewayLogger()
