"""Abstract provider interface — all providers must implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

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


class BaseProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name

    @abstractmethod
    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> ChatCompletionResponse:
        ...

    @abstractmethod
    async def chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> AsyncIterator[ChatCompletionStreamChunk]:
        ...

    @abstractmethod
    async def create_embedding(
        self,
        request: EmbeddingRequest,
        api_key: str,
    ) -> EmbeddingResponse:
        ...

    @abstractmethod
    async def generate_image(
        self,
        request: ImageGenerationRequest,
        api_key: str,
    ) -> ImageResponse:
        ...

    @abstractmethod
    async def create_speech(
        self,
        request: SpeechRequest,
        api_key: str,
    ) -> bytes:
        ...

    @abstractmethod
    async def create_transcription(
        self,
        request: TranscriptionRequest,
        api_key: str,
    ) -> TranscriptionResponse:
        ...

    @abstractmethod
    async def list_models(self, api_key: str) -> ModelsListResponse:
        ...

    async def health_check(self) -> bool:
        """Quick health check — returns True if the provider is reachable."""
        try:
            await self.list_models("")
            return True
        except Exception:
            return False
