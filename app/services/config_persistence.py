"""Config persistence — save runtime changes back to config.yaml."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from app.config.settings import get_config, reload_config

logger = logging.getLogger(__name__)


def _get_config_path() -> str:
    """Get the path to config.yaml."""
    # Check common locations
    candidates = [
        "config.yaml",
        "./config.yaml",
        "/app/config.yaml",
    ]
    for path in candidates:
        if Path(path).exists():
            return str(Path(path).resolve())
    return "config.yaml"


async def save_current_config() -> bool:
    """
    Save the current in-memory configuration back to config.yaml.

    This allows admin UI changes to persist across restarts.
    Returns True if successful.
    """
    try:
        config = get_config()
        config_path = _get_config_path()

        # Build the YAML dict from current AppConfig
        data = config.model_dump(mode="json", exclude_none=True)

        # Write with a backup
        if Path(config_path).exists():
            backup_path = config_path + ".bak"
            import shutil
            shutil.copy2(config_path, backup_path)

        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2, allow_unicode=True)

        logger.info("Configuration saved to %s", config_path)
        return True

    except Exception as e:
        logger.error("Failed to save configuration: %s", e)
        return False


async def get_config_yaml() -> str:
    """Get the current config.yaml content as a string."""
    config_path = _get_config_path()
    if Path(config_path).exists():
        with open(config_path, "r") as f:
            return f.read()
    return ""


async def update_config_yaml(yaml_content: str) -> bool:
    """
    Update config.yaml with new content.
    This is a full replace — use with caution.
    """
    try:
        config_path = _get_config_path()

        # Validate YAML first
        parsed = yaml.safe_load(yaml_content)
        if parsed is None:
            return False

        with open(config_path, "w") as f:
            f.write(yaml_content)

        # Reload into memory
        reload_config()
        logger.info("Configuration updated from YAML")
        return True

    except Exception as e:
        logger.error("Failed to update configuration: %s", e)
        return False
