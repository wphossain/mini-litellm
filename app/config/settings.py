"""
Configuration loader for Mini LiteLLM Gateway.

Parses config.yaml, resolves ${ENV_VAR} placeholders from environment,
and provides a singleton AppConfig instance with hot-reload support.

Handles Vercel serverless environment:
- Searches multiple paths for config.yaml
- Falls back to environment variables when config file is missing
"""

from __future__ import annotations

import os
import re
import logging
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from app.models.config_models import AppConfig, GatewayConfig, AuthConfig, ProviderConfig, \
    RateLimitConfig, CorsConfig, RateLimitingConfig, ModelRoutingConfig, \
    FallbackConfig, HealthCheckConfig, RotationConfig, CacheConfig, DashboardConfig

logger = logging.getLogger(__name__)

# Load .env file if it exists
load_dotenv()

_config_instance: AppConfig | None = None
_config_path: str = ""
_config_mtime: float = 0

_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

# Possible config file locations (searched in order)
_CONFIG_SEARCH_PATHS = [
    "config.yaml",
    "./config.yaml",
    "/app/config.yaml",
    "/etc/mini-litellm/config.yaml",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.yaml"),
]


def _resolve_env_vars(value: Any, env: dict[str, str] | None = None) -> Any:
    if env is None:
        env = dict(os.environ)
    if isinstance(value, str):
        def _replace(match: re.Match) -> str:
            var_expr = match.group(1)
            if ":-" in var_expr:
                var_name, default = var_expr.split(":-", 1)
            else:
                var_name = var_expr
                default = ""
            return env.get(var_name, default)
        return _ENV_VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v, env) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item, env) for item in value]
    return value


def _find_config_file() -> str:
    """Search for config.yaml across multiple locations."""
    for path in _CONFIG_SEARCH_PATHS:
        if Path(path).exists():
            return str(Path(path).resolve())
    return _CONFIG_SEARCH_PATHS[0]


def _build_default_config() -> AppConfig:
    """Build a minimal config from environment variables when no config.yaml exists.
    This enables Vercel deployment without a file-based config.
    """
    logger.warning("No config.yaml found. Building config from environment variables.")
    return AppConfig(
        gateway=GatewayConfig(
            name=os.environ.get("GATEWAY_NAME", "Mini LiteLLM Gateway"),
            port=int(os.environ.get("PORT", os.environ.get("GATEWAY_PORT", "4000"))),
            log_level=os.environ.get("GATEWAY_LOG_LEVEL", "INFO"),
        ),
        auth=AuthConfig(
            master_key=os.environ.get("GATEWAY_MASTER_KEY", ""),
            admin_key=os.environ.get("GATEWAY_ADMIN_KEY", "sk-admin-master"),
            readonly_key=os.environ.get("GATEWAY_READONLY_KEY", "sk-readonly"),
            disabled=os.environ.get("GATEWAY_AUTH_DISABLED", "").lower() == "true",
        ),
        providers=[
            ProviderConfig(
                name="openai", type="openai", enabled=True, priority=1,
                api_base="https://api.openai.com/v1",
                api_keys=[k for k in [os.environ.get("OPENAI_API_KEY", "")] if k],
            ),
            ProviderConfig(
                name="anthropic", type="anthropic", enabled=True, priority=2,
                api_base="https://api.anthropic.com",
                api_keys=[k for k in [os.environ.get("ANTHROPIC_API_KEY", "")] if k],
            ),
            ProviderConfig(
                name="gemini", type="gemini", enabled=True, priority=3,
                api_base="https://generativelanguage.googleapis.com",
                api_keys=[k for k in [os.environ.get("GEMINI_API_KEY", "")] if k],
            ),
            ProviderConfig(
                name="openrouter", type="openrouter", enabled=True, priority=4,
                api_base="https://openrouter.ai/api/v1",
                api_keys=[k for k in [os.environ.get("OPENROUTER_API_KEY", "")] if k],
            ),
        ],
        fallback=FallbackConfig(enabled=True, chain=["openai", "anthropic", "openrouter", "gemini"]),
    )


def load_config(config_path: str | None = None) -> AppConfig:
    global _config_path, _config_mtime, _config_instance

    if config_path is None:
        config_path = _find_config_file()

    _config_path = str(Path(config_path).resolve())

    if not Path(_config_path).exists():
        logger.warning("Config file not found at %s. Using env-based config.", _config_path)
        _config_instance = _build_default_config()
        return _config_instance

    with open(_config_path, "r") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"Empty configuration file: {_config_path}")

    env = dict(os.environ)
    resolved: dict[str, Any] = _resolve_env_vars(raw, env)

    # Resolve API keys
    if "providers" in resolved:
        for provider in resolved["providers"]:
            resolved_keys: list[str] = []
            for key in provider.get("api_keys", []):
                resolved_key = _resolve_env_vars(key, env)
                if resolved_key and resolved_key.strip():
                    resolved_keys.append(resolved_key.strip())
            provider["api_keys"] = resolved_keys

    _config_instance = AppConfig(**resolved)
    _config_mtime = Path(_config_path).stat().st_mtime

    logger.info(
        "Configuration loaded: %s (%d providers, %d aliases)",
        _config_instance.gateway.name,
        len(_config_instance.providers),
        len(_config_instance.model_aliases),
    )

    return _config_instance


def get_config() -> AppConfig:
    global _config_path, _config_mtime, _config_instance
    if _config_instance is None:
        return load_config()
    if _config_path and Path(_config_path).exists():
        current_mtime = Path(_config_path).stat().st_mtime
        if current_mtime > _config_mtime:
            logger.info("Configuration file changed, reloading...")
            return load_config(_config_path)
    return _config_instance


def reload_config() -> AppConfig:
    global _config_instance, _config_mtime
    _config_instance = None
    _config_mtime = 0
    return load_config(_config_path if _config_path else None)


def get_enabled_providers() -> list[ProviderConfig]:
    config = get_config()
    enabled = [p for p in config.providers if p.enabled]
    enabled.sort(key=lambda p: p.priority)
    return enabled


def resolve_model_alias(model: str) -> str:
    config = get_config()
    return config.model_aliases.get(model, model)


def get_provider_by_name(name: str) -> ProviderConfig | None:
    config = get_config()
    for provider in config.providers:
        if provider.name == name:
            return provider
    return None
