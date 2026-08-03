"""Core gateway service — request routing, dispatch, and lifecycle."""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncIterator

from app.config.settings import get_config, get_enabled_providers, resolve_model_alias, get_provider_by_name
from app.core.fallback import execute_with_fallback
from app.core.health_checker import health_checker
from app.core.load_balancer import load_balancer, LoadBalancer
from app.core.logger import gateway_logger
from app.core.retry import retry_with_backoff
from app.core.rotation import key_rotator
from app.models.config_models import ProviderConfig
from app.models.openai_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChunk,
    EmbeddingRequest,
    EmbeddingResponse,
    ImageGenerationRequest,
    ImageResponse,
    ModelsListResponse,
    SpeechRequest,
    TranscriptionRequest,
    TranscriptionResponse,
)
from app.providers.base import BaseProvider
from app.providers.registry import provider_registry
from app.utils.cost_calculator import estimate_cost

logger = logging.getLogger(__name__)


class GatewayService:
    """Central service coordinating all gateway operations."""

    def _get_provider_instance(self, provider_name: str) -> BaseProvider:
        config = get_provider_by_name(provider_name)
        if config is None:
            raise ValueError(f"Provider not found: {provider_name}")
        return provider_registry.get_or_create(config)

    def _get_api_key(self, provider_name: str) -> str:
        config = get_provider_by_name(provider_name)
        if config is None:
            raise ValueError(f"Provider not found: {provider_name}")
        return key_rotator.next_key(config)

    async def chat_completion(
        self, request: ChatCompletionRequest, client_ip: str | None = None
    ) -> ChatCompletionResponse:
        resolved_model = resolve_model_alias(request.model)
        request.model = resolved_model

        async def _do_chat(provider_name: str) -> ChatCompletionResponse:
            provider = self._get_provider_instance(provider_name)
            api_key = self._get_api_key(provider_name)
            start = time.monotonic()
            result, attempts = await retry_with_backoff(
                provider.chat_completion, request, api_key,
                max_retries=provider.config.max_retries,
            )
            latency_ms = (time.monotonic() - start) * 1000
            load_balancer.record_latency(provider_name, latency_ms)

            tokens = result.usage.total_tokens if result.usage else 0
            cost = estimate_cost(resolved_model, result.usage.prompt_tokens if result.usage else 0, result.usage.completion_tokens if result.usage else 0)

            await gateway_logger.log_request(
                method="POST", path="/v1/chat/completions",
                model=resolved_model, provider=provider_name,
                latency_ms=latency_ms, total_tokens=tokens,
                prompt_tokens=result.usage.prompt_tokens if result.usage else 0,
                completion_tokens=result.usage.completion_tokens if result.usage else 0,
                estimated_cost_usd=cost, client_ip=client_ip,
            )
            return result

        return await execute_with_fallback(_do_chat)

    async def chat_completion_stream(
        self, request: ChatCompletionRequest, client_ip: str | None = None
    ) -> AsyncIterator[ChatCompletionStreamChunk]:
        resolved_model = resolve_model_alias(request.model)
        request.model = resolved_model

        async def _do_stream(provider_name: str):
            provider = self._get_provider_instance(provider_name)
            api_key = self._get_api_key(provider_name)
            start = time.monotonic()
            async for chunk in provider.chat_completion_stream(request, api_key):
                yield chunk
            latency_ms = (time.monotonic() - start) * 1000
            load_balancer.record_latency(provider_name, latency_ms)
            await gateway_logger.log_request(
                method="POST", path="/v1/chat/completions",
                model=resolved_model, provider=provider_name,
                latency_ms=latency_ms, client_ip=client_ip,
            )

        # For streaming, use first available provider (fallback is complex with generators)
        providers = get_enabled_providers()
        if not providers:
            raise RuntimeError("No enabled providers")

        # Try each provider in the fallback chain
        config = get_config()
        chain = [p.name for p in providers]
        if config.fallback.enabled:
            chain = config.fallback.chain + [p.name for p in providers if p.name not in config.fallback.chain]

        last_error: Exception | None = None
        for provider_name in chain:
            provider_config = get_provider_by_name(provider_name)
            if provider_config is None or not provider_config.enabled:
                continue
            try:
                async for chunk in _do_stream(provider_name):
                    yield chunk
                return
            except Exception as e:
                last_error = e
                continue

        raise last_error or RuntimeError("All providers failed for streaming")

    async def create_embedding(self, request: EmbeddingRequest, client_ip: str | None = None) -> EmbeddingResponse:
        resolved_model = resolve_model_alias(request.model)
        request.model = resolved_model

        async def _do_embed(provider_name: str) -> EmbeddingResponse:
            provider = self._get_provider_instance(provider_name)
            api_key = self._get_api_key(provider_name)
            start = time.monotonic()
            result = await provider.create_embedding(request, api_key)
            latency_ms = (time.monotonic() - start) * 1000
            await gateway_logger.log_request(
                method="POST", path="/v1/embeddings",
                model=resolved_model, provider=provider_name,
                latency_ms=latency_ms, total_tokens=result.usage.total_tokens if result.usage else 0,
                client_ip=client_ip,
            )
            return result

        return await execute_with_fallback(_do_embed)

    async def generate_image(self, request: ImageGenerationRequest, client_ip: str | None = None) -> ImageResponse:
        async def _do_image(provider_name: str) -> ImageResponse:
            provider = self._get_provider_instance(provider_name)
            api_key = self._get_api_key(provider_name)
            result = await provider.generate_image(request, api_key)
            return result

        return await execute_with_fallback(_do_image)

    async def create_speech(self, request: SpeechRequest) -> bytes:
        async def _do_speech(provider_name: str) -> bytes:
            provider = self._get_provider_instance(provider_name)
            api_key = self._get_api_key(provider_name)
            return await provider.create_speech(request, api_key)

        return await execute_with_fallback(_do_speech)

    async def create_transcription(self, request: TranscriptionRequest) -> TranscriptionResponse:
        async def _do_transcription(provider_name: str) -> TranscriptionResponse:
            provider = self._get_provider_instance(provider_name)
            api_key = self._get_api_key(provider_name)
            return await provider.create_transcription(request, api_key)

        return await execute_with_fallback(_do_transcription)

    async def list_models(self) -> ModelsListResponse:
        config = get_config()
        all_entries = []
        seen = set()

        for alias_name, target in config.model_aliases.items():
            from app.models.openai_models import ModelEntry
            all_entries.append(ModelEntry(id=alias_name, owned_by="mini-litellm"))
            seen.add(alias_name)
            seen.add(target)

        for provider_config in get_enabled_providers():
            health = health_checker.get_health(provider_config.name)
            if health.status == "unhealthy":
                continue
            try:
                provider = provider_registry.get_or_create(provider_config)
                api_key = key_rotator.next_key(provider_config)
                result = await provider.list_models(api_key)
                for entry in result.data:
                    if entry.id not in seen:
                        all_entries.append(entry)
                        seen.add(entry.id)
            except Exception:
                continue

        if not all_entries:
            for provider_config in get_enabled_providers():
                from app.models.openai_models import ModelEntry
                all_entries.append(ModelEntry(id=f"{provider_config.name}/*", owned_by=provider_config.name))

        return ModelsListResponse(data=all_entries)


gateway_service = GatewayService()
