"""Admin REST API — provider management, API keys, logs, and statistics."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.config.settings import get_config, reload_config, get_enabled_providers
from app.core.auth import require_admin
from app.core.health_checker import health_checker
from app.core.logger import gateway_logger
from app.models.stats_models import AdminProviderRequest, AdminKeyRequest, AdminToggleRequest, ProviderUsageStats
from app.providers.registry import provider_registry
from app.services.log_service import log_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin")


# ---- Auth check for all admin routes ----

@router.get("/me", summary="Verify admin authentication", tags=["Admin"])
async def admin_me(request: Request):
    token = await require_admin(request)
    return {"authenticated": True, "token_prefix": token[:8] + "..."}


# ---- Providers ----

@router.get("/providers", summary="List all providers", tags=["Admin"])
async def list_providers(request: Request):
    await require_admin(request)
    config = get_config()
    result = []
    for p in config.providers:
        health = health_checker.get_health(p.name)
        result.append({
            "name": p.name,
            "type": p.type,
            "enabled": p.enabled,
            "priority": p.priority,
            "api_base": p.api_base,
            "api_keys_count": len(p.api_keys),
            "models": p.models,
            "cost_weight": p.cost_weight,
            "latency_weight": p.latency_weight,
            "status": health.status,
            "consecutive_failures": health.consecutive_failures,
            "avg_latency_ms": health.avg_latency_ms,
        })
    return result


@router.post("/providers", summary="Add a new provider", tags=["Admin"])
async def add_provider(request: Request, body: AdminProviderRequest):
    await require_admin(request)
    config = get_config()

    for p in config.providers:
        if p.name == body.name:
            raise HTTPException(status_code=400, detail=f"Provider '{body.name}' already exists")

    from app.models.config_models import ProviderConfig, RateLimitConfig
    new_provider = ProviderConfig(
        name=body.name,
        type=body.type,
        enabled=body.enabled,
        priority=body.priority,
        api_base=body.api_base,
        api_keys=body.api_keys,
        api_version=body.api_version,
        models=body.models,
        cost_weight=body.cost_weight,
        latency_weight=body.latency_weight,
        max_retries=body.max_retries,
        timeout=body.timeout,
        rate_limit=RateLimitConfig(
            requests_per_minute=body.requests_per_minute,
            tokens_per_minute=body.tokens_per_minute,
        ),
    )
    config.providers.append(new_provider)
    return {"status": "added", "provider": body.name}


@router.delete("/providers/{provider_name}", summary="Delete a provider", tags=["Admin"])
async def delete_provider(request: Request, provider_name: str):
    await require_admin(request)
    config = get_config()
    before = len(config.providers)
    config.providers = [p for p in config.providers if p.name != provider_name]
    if len(config.providers) == before:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    provider_registry.remove(provider_name)
    return {"status": "deleted", "provider": provider_name}


@router.post("/providers/toggle", summary="Enable or disable a provider", tags=["Admin"])
async def toggle_provider(request: Request, body: AdminToggleRequest):
    await require_admin(request)
    config = get_config()
    for p in config.providers:
        if p.name == body.provider_name:
            p.enabled = body.enabled
            return {"status": "enabled" if body.enabled else "disabled", "provider": body.provider_name}
    raise HTTPException(status_code=404, detail=f"Provider '{body.provider_name}' not found")


@router.post("/providers/reload", summary="Reload configuration from disk", tags=["Admin"])
async def reload_providers(request: Request):
    await require_admin(request)
    provider_registry.clear()
    config = reload_config()
    return {"status": "reloaded", "providers": len(config.providers)}


# ---- API Keys ----

@router.post("/keys", summary="Add API key to a provider", tags=["Admin"])
async def add_key(request: Request, body: AdminKeyRequest):
    await require_admin(request)
    config = get_config()
    for p in config.providers:
        if p.name == body.provider_name:
            if body.api_key not in p.api_keys:
                p.api_keys.append(body.api_key)
            return {"status": "added", "provider": body.provider_name, "keys_count": len(p.api_keys)}
    raise HTTPException(status_code=404, detail=f"Provider '{body.provider_name}' not found")


@router.delete("/keys", summary="Remove an API key from a provider", tags=["Admin"])
async def delete_key(request: Request, body: AdminKeyRequest):
    await require_admin(request)
    config = get_config()
    for p in config.providers:
        if p.name == body.provider_name:
            if body.api_key in p.api_keys:
                p.api_keys.remove(body.api_key)
            return {"status": "deleted", "provider": body.provider_name, "keys_count": len(p.api_keys)}
    raise HTTPException(status_code=404, detail=f"Provider '{body.provider_name}' not found")


# ---- Logs & Stats ----

@router.get("/logs", summary="Get recent request logs", tags=["Admin"])
async def get_logs(request: Request, limit: int = 100, offset: int = 0):
    await require_admin(request)
    logs, total = await log_service.get_recent_logs(limit=limit, offset=offset)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": [l.model_dump(mode="json") for l in logs],
    }


@router.get("/stats", summary="Get gateway statistics", tags=["Admin"])
async def get_stats(request: Request):
    await require_admin(request)
    return await log_service.get_stats()


@router.delete("/logs", summary="Clear all logs", tags=["Admin"])
async def clear_logs(request: Request):
    await require_admin(request)
    count = await log_service.clear_logs()
    return {"status": "cleared", "deleted_count": count}


# ---- Health (Admin) ----

@router.get("/health", summary="Admin health overview", tags=["Admin"])
async def admin_health(request: Request):
    await require_admin(request)
    return {
        "providers": [h.model_dump() for h in health_checker.get_all_health()],
        "stats": await log_service.get_stats(),
    }
