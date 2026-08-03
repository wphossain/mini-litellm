"""LiteLLM SDK integration — lazy-imports litellm to avoid heavy import on Vercel cold start."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, AsyncIterator

import litellm  # Imported at module level (fine on most platforms)

from app.models.config_models import ProviderConfig
from app.models.openai_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChunk,
    ChatChoice,
    ChatMessage,
    ChatStreamChoice,
    DeltaContent,
    EmbeddingData,
    EmbeddingRequest,
    EmbeddingResponse,
    ImageData,
    ImageGenerationRequest,
    ImageResponse,
    ModelEntry,
    ModelsListResponse,
    SpeechRequest,
    TranscriptionRequest,
    TranscriptionResponse,
    Usage,
)
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


def _get_litellm():
    """Get the litellm module — lazily imported for Vercel cold-start."""
    return litellm


class LiteLLMProvider(BaseProvider):
    """
    Universal provider that wraps LiteLLM SDK.
    Handles all provider types through a single code path.
    """

    def _get_completion_kwargs(self, api_key: str) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": self.config.timeout,
        }
        if self.config.api_base:
            kwargs["api_base"] = self.config.api_base
        if self.config.api_version:
            kwargs["api_version"] = self.config.api_version
        kwargs.update(self.config.extra_params)
        return kwargs

    def _extract_model_name(self, model: str) -> str:
        if "/" in model:
            return model.split("/", 1)[1]
        return model

    async def chat_completion(self, request: ChatCompletionRequest, api_key: str) -> ChatCompletionResponse:
        kwargs = self._get_completion_kwargs(api_key)
        model = self._extract_model_name(request.model)
        messages = [m.model_dump(exclude_none=True) for m in request.messages]
        lm = _get_litellm()
        response = await lm.acompletion(
            model=model, messages=messages,
            temperature=request.temperature, top_p=request.top_p,
            n=request.n, max_tokens=request.max_tokens or request.max_completion_tokens,
            stop=request.stop, stream=False,
            presence_penalty=request.presence_penalty, frequency_penalty=request.frequency_penalty,
            user=request.user, **kwargs,
        )
        choice = response.choices[0]
        msg = choice.message
        return ChatCompletionResponse(
            id=response.id or f"chatcmpl-{uuid.uuid4().hex[:12]}",
            model=response.model or request.model,
            choices=[ChatChoice(
                index=choice.index,
                message=ChatMessage(role=msg.role or "assistant", content=msg.content,
                                    function_call=msg.function_call, tool_calls=msg.tool_calls),
                finish_reason=choice.finish_reason,
            )],
            usage=Usage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            ),
        )

    async def chat_completion_stream(self, request: ChatCompletionRequest, api_key: str) -> AsyncIterator[ChatCompletionStreamChunk]:
        kwargs = self._get_completion_kwargs(api_key)
        model = self._extract_model_name(request.model)
        messages = [m.model_dump(exclude_none=True) for m in request.messages]
        lm = _get_litellm()
        response = await lm.acompletion(
            model=model, messages=messages,
            temperature=request.temperature, top_p=request.top_p,
            n=request.n, max_tokens=request.max_tokens or request.max_completion_tokens,
            stop=request.stop, stream=True,
            presence_penalty=request.presence_penalty, frequency_penalty=request.frequency_penalty,
            user=request.user, **kwargs,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0]:
                c = chunk.choices[0]
                delta = c.delta
                yield ChatCompletionStreamChunk(
                    id=chunk.id or f"chatcmpl-{uuid.uuid4().hex[:12]}",
                    model=chunk.model or request.model,
                    choices=[ChatStreamChoice(
                        index=c.index or 0,
                        delta=DeltaContent(
                            content=delta.content if delta else None,
                            role=delta.role if delta else None,
                            function_call=delta.function_call if delta else None,
                            tool_calls=delta.tool_calls if delta else None,
                        ),
                        finish_reason=c.finish_reason,
                    )],
                )

    async def create_embedding(self, request: EmbeddingRequest, api_key: str) -> EmbeddingResponse:
        kwargs = self._get_completion_kwargs(api_key)
        model = self._extract_model_name(request.model)
        inp = request.input if isinstance(request.input, list) else [request.input]
        lm = _get_litellm()
        response = await lm.aembedding(model=model, input=inp, **kwargs)
        data = [EmbeddingData(index=d.get("index", i), embedding=d.get("embedding", []))
                for i, d in enumerate(response.data)]
        return EmbeddingResponse(
            model=response.model or request.model, data=data,
            usage=Usage(prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                        total_tokens=response.usage.total_tokens if response.usage else 0),
        )

    async def generate_image(self, request: ImageGenerationRequest, api_key: str) -> ImageResponse:
        kwargs = self._get_completion_kwargs(api_key)
        model = self._extract_model_name(request.model)
        lm = _get_litellm()
        response = await lm.aimage_generation(model=model, prompt=request.prompt, n=request.n, size=request.size, **kwargs)
        data = [ImageData(url=d.get("url"), b64_json=d.get("b64_json"), revised_prompt=d.get("revised_prompt"))
                for d in (response.data or [])]
        return ImageResponse(data=data)

    async def create_speech(self, request: SpeechRequest, api_key: str) -> bytes:
        kwargs = self._get_completion_kwargs(api_key)
        model = self._extract_model_name(request.model)
        lm = _get_litellm()
        response = await lm.aspeech(model=model, input=request.input, voice=request.voice,
                                     response_format=request.response_format, speed=request.speed, **kwargs)
        if hasattr(response, "content"):
            return response.content
        return response if isinstance(response, bytes) else b""

    async def create_transcription(self, request: TranscriptionRequest, api_key: str) -> TranscriptionResponse:
        kwargs = self._get_completion_kwargs(api_key)
        model = self._extract_model_name(request.model)
        lm = _get_litellm()
        response = await lm.atranscription(model=model, file=request.file, language=request.language,
                                            prompt=request.prompt, temperature=request.temperature, **kwargs)
        text = response.text if hasattr(response, "text") else str(response)
        return TranscriptionResponse(text=text)

    async def list_models(self, api_key: str) -> ModelsListResponse:
        if self.config.models:
            return ModelsListResponse(data=[ModelEntry(id=m, owned_by=self.config.name) for m in self.config.models])
        try:
            kwargs = self._get_completion_kwargs(api_key)
            kwargs.pop("timeout", None)
            lm = _get_litellm()
            if api_key:
                response = lm.get_model_list(api_key=api_key, **kwargs) if api_key else {}
                model_ids = response.get("data", []) if isinstance(response, dict) else []
                entries = [ModelEntry(id=m.get("id", f"{self.config.name}/unknown"), owned_by=m.get("owned_by", self.config.name))
                           for m in (model_ids if isinstance(model_ids, list) else [])]
                return ModelsListResponse(data=entries) if entries else ModelsListResponse(data=[])
        except Exception as e:
            logger.debug("Could not fetch model list for '%s': %s", self.config.name, e)
        return ModelsListResponse(data=[])
