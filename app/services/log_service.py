"""Log management service — retrieval, cleanup, and disk persistence."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.core.logger import gateway_logger
from app.models.stats_models import RequestLog

logger = logging.getLogger(__name__)


class LogService:
    """Service for managing logs."""

    async def get_recent_logs(self, limit: int = 100, offset: int = 0) -> tuple[list[RequestLog], int]:
        return await gateway_logger.get_logs(limit=limit, offset=offset)

    async def get_stats(self):
        return await gateway_logger.get_stats()

    async def save_to_file(self, filepath: str = "logs/gateway_logs.json") -> str:
        await gateway_logger.save_to_file(filepath)
        return filepath

    async def clear_logs(self) -> int:
        count = len(gateway_logger._logs)
        await gateway_logger.clear()
        return count

    async def cleanup_old_logs(self, retention_days: int = 7) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        async with gateway_logger._lock:
            before = len(gateway_logger._logs)
            gateway_logger._logs = [
                log for log in gateway_logger._logs
                if log.timestamp.replace(tzinfo=timezone.utc) > cutoff
            ]
            return before - len(gateway_logger._logs)


log_service = LogService()
