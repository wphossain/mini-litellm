"""Pydantic models for YAML configuration parsing."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RateLimitConfig(BaseModel):
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000


class ProviderConfig(BaseModel):
    name: str
    type: str
    enabled: bool = True
    priority: int = 10
    api_base: str = ""
    api_keys: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    api_version: str | None = None
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    cost_weight: int = 0
    latency_weight: int = 0
    max_retries: int = 3
    timeout: int = 120
    extra_params: dict[str, Any] = Field(default_factory=dict)


class GatewayConfig(BaseModel):
    name: str = "Mini LiteLLM Gateway"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 4000
    log_level: str = "INFO"
    log_to_file: bool = False
    log_retention_days: int = 7
    max_request_size: int = 10_485_760
    request_timeout: int = 300
    streaming_enabled: bool = True


class AuthConfig(BaseModel):
    master_key: str = ""
    admin_key: str = "sk-admin-master"
    readonly_key: str = "sk-readonly"
    disabled: bool = False


class RateLimitingConfig(BaseModel):
    enabled: bool = True
    strategy: str = "token_bucket"
    requests_per_minute: int = 60
    burst_size: int = 20


class CorsConfig(BaseModel):
    enabled: bool = True
    allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    allow_credentials: bool = True


class ModelRoutingConfig(BaseModel):
    preferred_provider: str = ""
    prefer_lowest_cost: bool = False
    prefer_lowest_latency: bool = False
    max_retries_per_request: int = 3


class FallbackConfig(BaseModel):
    enabled: bool = True
    chain: list[str] = Field(default_factory=list)


class HealthCheckConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = 60
    timeout_seconds: int = 10
    consecutive_failures: int = 3
    recovery_attempts: int = 5
    endpoints: dict[str, str] = Field(default_factory=dict)


class RotationConfig(BaseModel):
    strategy: str = "round_robin"
    failover_on_error: bool = True
    reset_on_success: bool = True


class CacheConfig(BaseModel):
    model_list_ttl: int = 300
    response_cache: bool = False
    response_cache_ttl: int = 60


class DashboardConfig(BaseModel):
    enabled: bool = False
    path: str = "./dashboard/dist"
    static_url: str = "/admin/ui"


class AppConfig(BaseModel):
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    rate_limiting: RateLimitingConfig = Field(default_factory=RateLimitingConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    model_aliases: dict[str, str] = Field(default_factory=dict)
    model_routing: ModelRoutingConfig = Field(default_factory=ModelRoutingConfig)
    providers: list[ProviderConfig] = Field(default_factory=list)
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    rotation: RotationConfig = Field(default_factory=RotationConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
