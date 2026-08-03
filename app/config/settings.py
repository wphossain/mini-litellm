"""
Configuration loader for Mini LiteLLM Gateway.

Parses config.yaml, resolves ${ENV_VAR} placeholders from environment,
and provides a singleton AppConfig instance with hot-reload support.
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
    """Resolve API keys for providers, filtering out empty keys."""
    for provider in providers:
        resolved_keys: list[str] = []
        for key in provider.get("api_keys", []):
            resolved = _resolve_env_vars(key, env)
            if resolved and resolved.strip():
                resolved_keys.append(resolved.strip())
        provider["api_keys"] = resolved_keys
    return providers


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """
    Load and parse the YAML configuration file.

    Resolution order:
    1. YAML file with ${ENV_VAR} placeholders
    2. .env file (loaded via python-dotenv)
    3. Actual OS environment variables
    """
    global _config_path, _config_mtime, _config_instance

    _config_path = str(Path(config_path).resolve())

    if not Path(_config_path).exists():
        raise FileNotFoundError(f"Configuration file not found: {_config_path}")

    with open(_config_path, "r") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"Empty configuration file: {_config_path}")

    env = dict(os.environ)

    # Resolve env vars at every level
    resolved: dict[str, Any] = _resolve_env_vars(raw, env)

    # Resolve API keys specifically
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

    if _config_path and Path(_config_path).exists():
        current_mtime = Path(_config_path).stat().st_mtime
        if current_mtime > _config_mtime:
            logger.info("Configuration file changed, reloading...")
            return load_config(_config_path)

    return _config_instance


def reload_config() -> AppConfig:
    """Force reload the configuration from disk."""
    global _config_instance, _config_mtime
    _config_instance = None
    _config_mtime = 0
    return load_config(_config_path if _config_path else "config.yaml")


def get_enabled_providers() -> list[ProviderConfig]:
    """Get all enabled providers sorted by priority."""
    config = get_config()
    enabled = [p for p in config.providers if p.enabled]
    enabled.sort(key=lambda p: p.priority)
    return enabled


def resolve_model_alias(model: str) -> str:
    """Resolve a model alias to its full provider/model string."""
    config = get_config()
    return config.model_aliases.get(model, model)


def get_provider_by_name(name: str) -> ProviderConfig | None:
    """Get a provider configuration by name."""
    config = get_config()
    for provider in config.providers:
        if provider.name == name:
            return provider
    return None
