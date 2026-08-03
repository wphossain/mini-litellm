"""Provider registry — manages provider lifecycle and plugin registration."""

from __future__ import annotations

import logging
from typing import Type

from app.models.config_models import ProviderConfig
from app.providers.base import BaseProvider
from app.providers.litellm_sdk import LiteLLMProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Central registry for managing provider instances."""

    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}
        self._provider_classes: dict[str, Type[BaseProvider]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register built-in provider types."""
        builtins = [
            "openai", "anthropic", "gemini", "openrouter", "mistral",
            "groq", "deepseek", "azure", "ollama", "openai_compatible",
            "nvidia", "vertex", "bedrock", "vllm", "lm_studio", "xinference",
        ]
        for name in builtins:
            self._provider_classes[name] = LiteLLMProvider

    def register_provider_class(self, provider_type: str, cls: Type[BaseProvider]) -> None:
        """Register a custom provider class."""
        self._provider_classes[provider_type] = cls
        logger.info("Registered provider class for '%s': %s", provider_type, cls.__name__)

    def get_or_create(self, config: ProviderConfig) -> BaseProvider:
        """Get an existing provider instance or create a new one."""
        if config.name in self._providers:
            return self._providers[config.name]

        provider_cls = self._provider_classes.get(config.type)
        if provider_cls is None:
            logger.warning(
                "Unknown provider type '%s' for '%s', defaulting to LiteLLMProvider",
                config.type, config.name,
            )
            provider_cls = LiteLLMProvider

        instance = provider_cls(config)
        self._providers[config.name] = instance
        logger.info("Created provider '%s' (type=%s)", config.name, config.type)
        return instance

    def get(self, name: str) -> BaseProvider | None:
        """Get an existing provider by name."""
        return self._providers.get(name)

    def remove(self, name: str) -> bool:
        """Remove a provider from the registry."""
        if name in self._providers:
            del self._providers[name]
            logger.info("Removed provider '%s' from registry", name)
            return True
        return False

    def list_all(self) -> list[str]:
        """Get names of all registered providers."""
        return list(self._providers.keys())

    def clear(self) -> None:
        """Remove all providers."""
        self._providers.clear()
        logger.info("Cleared all providers from registry")


provider_registry = ProviderRegistry()
