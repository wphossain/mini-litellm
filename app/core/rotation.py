"""API Key rotation strategies: round_robin, random, least_used, priority."""

from __future__ import annotations

import random
import threading
from collections import defaultdict

from app.config.settings import get_config
from app.models.config_models import ProviderConfig


class KeyRotator:
    """Rotates multiple API keys for a single provider."""

    def __init__(self):
        self._indexes: dict[str, int] = defaultdict(int)
        self._usage_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._lock = threading.Lock()

    def next_key(self, provider: ProviderConfig) -> str:
        """Get the next API key for a provider based on configured strategy."""
        keys = provider.api_keys
        if not keys:
            return ""
        if len(keys) == 1:
            return keys[0]

        config = get_config()
        strategy = config.rotation.strategy

        with self._lock:
            if strategy == "random":
                return random.choice(keys)
            elif strategy == "least_used":
                provider_usage = self._usage_counts[provider.name]
                best_key = min(keys, key=lambda k: provider_usage.get(k, 0))
                provider_usage[best_key] += 1
                return best_key
            elif strategy == "priority":
                return keys[0]
            else:
                idx = self._indexes[provider.name]
                key = keys[idx % len(keys)]
                self._indexes[provider.name] = idx + 1
                return key

    def mark_failure(self, provider: ProviderConfig, key: str) -> None:
        with self._lock:
            self._indexes[provider.name] = self._indexes.get(provider.name, 0) + 1

    def mark_success(self, provider: ProviderConfig, key: str) -> None:
        if not get_config().rotation.reset_on_success:
            return
        with self._lock:
            self._usage_counts[provider.name][key] += 1


key_rotator = KeyRotator()
