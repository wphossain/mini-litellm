"""
Configuration loader for Mini LiteLLM Gateway.

Parses config.yaml, resolves ${ENV_VAR} placeholders from environment,
and provides a singleton AppConfig instance with hot-reload support.

Works on Vercel serverless too — falls back to defaults if config.yaml is missing.
"""

from __future__ import annotations

import os
import re
import logging
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from app.models.config_models import AppConfig, ProviderConfig

logger = logging.getLogger(__name__)

# Load .env file if it exists
load_dotenv()

_config_instance: AppConfig | None = None
_config_path: str = ""
_config_mtime: float = 0

_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_vars(value: Any, env: dict[str, str] | None = None) -> Any:
    """Recursively resolve ${ENV_VAR} patterns in config values."""
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


def _resolve_provider_api_keys(providers: list[dict[str, Any]], env: dict[str, str]) -> list[dict[str, Any]]:
    for provider in providers:
        resolved_keys: list[str] = []
        for key in provider.get("api_keys", []):
            resolved = _resolve_env_vars(key, env)
            if resolved and resolved.strip():
                resolved_keys.append(resolved.strip())
        provider["api_keys"] = resolved_keys
    return providers


def _find_config_file() -> str:
    """Find config.yaml in possible locations."""
    candidates = [
        "config.yaml",
        "./config.yaml",
        os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml"),
        "/app/config.yaml",  # Vercel / Docker path
    ]
    for path in candidates:
        resolved = str(Path(path).resolve())
        if Path(resolved).exists():
            return resolved
    return ""


def _make_default_config() -> AppConfig:
    """Create a default config from environment variables when config.yaml is missing.
    This is essential for Vercel serverless where config.yaml may not be deployed."""
    # Build a simple provider from env vars
    providers_list: list[dict[str, Any]] = []

    provider_mapping = {
        "OPENAI_API_KEY": ("openai", "openai", "https://api.openai.com/v1", 1),
        "ANTHROPIC_API_KEY": ("anthropic", "anthropic", "https://api.anthropic.com", 2),
        "GEMINI_API_KEY": ("gemini", "gemini", "https://generativelanguage.googleapis.com", 3),
        "OPENROUTER_API_KEY": ("openrouter", "openrouter", "https://openrouter.ai/api/v1", 4),
        "MISTRAL_API_KEY": ("mistral", "mistral", "https://api.mistral.ai/v1", 5),
        "GROQ_API_KEY": ("groq", "groq", "https://api.groq.com/openai/v1", 6),
        "DEEPSEEK_API_KEY": ("deepseek", "deepseek", "https://api.deepseek.com", 7),
    }

    for env_var, (name, ptype, api_base, priority) in provider_mapping.items():
        key = os.environ.get(env_var, "")
        if key:
            providers_list.append({
                "name": name,
                "type": ptype,
                "enabled": True,
                "priority": priority,
                "api_base": api_base,
                "api_keys": [key],
                "models": [],
                "rate_limit": {"requests_per_minute": 100, "tokens_per_minute": 100000},
                "cost_weight": 0,
                "latency_weight": 0,
                "max_retries": 3,
                "timeout": 120,
            })

    default = {
        "gateway": {
            "name": "Mini LiteLLM Gateway",
            "version": "1.0.0",
            "host": "0.0.0.0",
            "port": int(os.environ.get("PORT", "4000")),
            "log_level": os.environ.get("GATEWAY_LOG_LEVEL", "INFO"),
            "streaming_enabled": True,
        },
        "auth": {
            "master_key": os.environ.get("GATEWAY_MASTER_KEY", "sk-master-key-change-me"),
            "admin_key": os.environ.get("GATEWAY_ADMIN_KEY", "sk-admin-master"),
            "readonly_key": os.environ.get("GATEWAY_READONLY_KEY", "sk-readonly"),
            "disabled": False,
        },
        "rate_limiting": {"enabled": False, "strategy": "token_bucket", "requests_per_minute": 60, "burst_size": 20},
        "cors": {
            "enabled": True,
            "allow_origins": ["*"],
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["*"],
            "allow_credentials": True,
        },
        "model_aliases": {
            "gpt-4o-mini": "openai/gpt-4o-mini",
            "gpt-4o": "openai/gpt-4o",
            "claude-sonnet": "anthropic/claude-sonnet-4-20250514",
            "claude-haiku": "anthropic/claude-haiku-3-5-20241022",
            "gemini-flash": "gemini/gemini-2.0-flash-exp",
            "deepseek-chat": "deepseek/deepseek-chat",
        },
        "model_routing": {"preferred_provider": "", "prefer_lowest_cost": False, "prefer_lowest_latency": False, "max_retries_per_request": 3},
        "providers": providers_list,
        "fallback": {
            "enabled": True,
            "chain": [p["name"] for p in providers_list],
        },
        "health_check": {
            "enabled": True,
            "interval_seconds": 60,
            "timeout_seconds": 10,
            "consecutive_failures": 3,
            "recovery_attempts": 5,
            "endpoints": {},
        },
        "rotation": {"strategy": "round_robin", "failover_on_error": True, "reset_on_success": True},
        "cache": {"model_list_ttl": 300, "response_cache": False, "response_cache_ttl": 60},
        "dashboard": {"enabled": False, "path": "./dashboard/dist", "static_url": "/admin/ui"},
    }

    return AppConfig(**default)


def load_config(config_path: str | None = None) -> AppConfig:
    """
    Load and parse the YAML configuration file.
    Falls back to environment-vars-only config on Vercel/serverless.
    """
    global _config_path, _config_mtime, _config_instance

    # Try provided path, then search for config.yaml
    if config_path:
        _config_path = str(Path(config_path).resolve())
    else:
        _config_path = _find_config_file()

    if not _config_path or not Path(_config_path).exists():
        logger.warning("config.yaml not found. Using environment-variable-based config.")
        _config_instance = _make_default_config()
        _config_mtime = 0
        return _config_instance

    try:
        with open(_config_path, "r") as f:
            raw: dict[str, Any] = yaml.safe_load(f)
    except Exception as e:
        logger.warning("Failed to load config.yaml: %s. Falling back to env config.", e)
        _config_instance = _make_default_config()
        return _config_instance

    if raw is None:
        logger.warning("Empty config.yaml. Falling back to env config.")
        _config_instance = _make_default_config()
        return _config_instance

    env = dict(os.environ)
    resolved: dict[str, Any] = _resolve_env_vars(raw, env)

    if "providers" in resolved:
        resolved["providers"] = _resolve_provider_api_keys(resolved["providers"], env)

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
    """Get the current configuration singleton with auto-reload."""
    global _config_path, _config_mtime, _config_instance
    if _config_instance is None:
        return load_config()
    return _config_instance


def reload_config() -> AppConfig:
    global _config_instance, _config_mtime
    _config_instance = None
    _config_mtime = 0
    return load_config()


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
