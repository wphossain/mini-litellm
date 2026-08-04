"""Health check endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter

from app.config.settings import get_config, get_enabled_providers
from app.core.health_checker import health_checker

router = APIRouter()

_start_time = time.time()


@router.get("/health", summary="Gateway health status", tags=["Health"])
async def health():
    config = get_config()
    providers = get_enabled_providers()
    unhealthy = [
        h for h in health_checker.get_all_health()
        if h.status == "unhealthy"
    ]
    return {
        "status": "ok" if not unhealthy else "degraded",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "version": config.gateway.version,
        "providers": {
            "total": len(config.providers),
            "enabled": len(providers),
            "unhealthy": len(unhealthy),
        },
    }


@router.get("/health/readiness", summary="Kubernetes readiness probe", tags=["Health"])
async def readiness():
    return {"status": "ready"}


@router.get("/health/liveness", summary="Kubernetes liveness probe", tags=["Health"])
async def liveness():
    return {"status": "alive"}


@router.get("/health/providers", summary="All provider health statuses", tags=["Health"])
async def provider_health():
    return [h.model_dump() for h in health_checker.get_all_health()]
