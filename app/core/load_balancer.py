"""Load balancer with 5 strategies: round_robin, random, weighted, priority, latency_based."""

from __future__ import annotations

import random
import threading
from collections import defaultdict

from app.models.config_models import ProviderConfig


class LoadBalancer:
    """Distributes requests across providers."""

    def __init__(self):
        self._indexes: dict[str, int] = defaultdict(int)
        self._latency_scores: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def select_provider(
        self,
        providers: list[ProviderConfig],
        strategy: str = "round_robin",
        preferred: str | None = None,
    ) -> ProviderConfig | None:
        if not providers:
            return None
        if len(providers) == 1:
            return providers[0]

        with self._lock:
            if strategy == "random":
                return random.choice(providers)
            elif strategy == "weighted":
                return self._weighted_select(providers)
            elif strategy == "priority":
                sorted_providers = sorted(providers, key=lambda p: p.priority)
                if preferred:
                    for p in sorted_providers:
                        if p.name == preferred:
                            return p
                return sorted_providers[0]
            elif strategy == "latency_based":
                return self._latency_select(providers)
            else:
                idx = self._indexes["global"]
                provider = providers[idx % len(providers)]
                self._indexes["global"] = idx + 1
                return provider

    def _weighted_select(self, providers: list[ProviderConfig]) -> ProviderConfig:
        weights = [max(0.1, 10.0 - p.cost_weight) for p in providers]
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0.0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                return providers[i]
        return providers[-1]

    def _latency_select(self, providers: list[ProviderConfig]) -> ProviderConfig:
        best_provider = providers[0]
        best_latency = float("inf")
        for p in providers:
            scores = self._latency_scores.get(p.name, [])
            avg = sum(scores[-10:]) / len(scores[-10:]) if scores else 0
            if avg < best_latency:
                best_latency = avg
                best_provider = p
        return best_provider

    def record_latency(self, provider_name: str, latency_ms: float) -> None:
        with self._lock:
            self._latency_scores[provider_name].append(latency_ms)
            if len(self._latency_scores[provider_name]) > 100:
                self._latency_scores[provider_name] = self._latency_scores[provider_name][-100:]

    def reset(self) -> None:
        with self._lock:
            self._indexes.clear()
            self._latency_scores.clear()


load_balancer = LoadBalancer()
