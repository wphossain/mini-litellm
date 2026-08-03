"""Statistics, health, and usage tracking models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class RequestLog(BaseModel):
    """A single logged request entry."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    method: str
    path: str
    model: str | None = None
    provider: str | None = None
    status_code: int = 200
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    error: str | None = None
    client_ip: str | None = None
    api_key_label: str | None = None


class ProviderHealth(BaseModel):
    """Health status for a single provider."""
    name: str
    status: Literal["healthy", "degraded", "unhealthy", "disabled"] = "healthy"
    last_check: datetime | None = None
    consecutive_failures: int = 0
    avg_latency_ms: float = 0.0
    error_message: str | None = None


class GatewayStats(BaseModel):
    """Aggregated gateway statistics."""
    uptime_seconds: float = 0.0
    total_requests: int = 0
    total_errors: int = 0
    total_tokens: int = 0
    estimated_total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    requests_per_minute: float = 0.0
    active_providers: int = 0
    total_providers: int = 0


class ProviderUsageStats(BaseModel):
    """Per-provider usage statistics."""
    provider_name: str
    total_requests: int = 0
    total_errors: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0


class AdminProviderRequest(BaseModel):
    """Request body for adding/updating a provider via admin API."""
    name: str
    type: str
    enabled: bool = True
    priority: int = 10
    api_base: str = ""
    api_keys: list[str] = Field(default_factory=list)
    api_version: str | None = None
    models: list[str] = Field(default_factory=list)
    cost_weight: int = 0
    latency_weight: int = 0
    max_retries: int = 3
    timeout: int = 120
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000


class AdminKeyRequest(BaseModel):
    """Request body for adding/removing an API key."""
    provider_name: str
    api_key: str


class AdminToggleRequest(BaseModel):
    """Request body for enabling/disabling a provider."""
    provider_name: str
    enabled: bool
