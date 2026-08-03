"""OpenAI-compatible request/response Pydantic models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---- Chat Completions ----

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "function", "tool"]
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    function_call: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class FunctionDef(BaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolDef(BaseModel):
    type: Literal["function"] = "function"
    function: FunctionDef


class ResponseFormat(BaseModel):
    type: Literal["text", "json_object", "json_schema"] = "text"
    json_schema: dict[str, Any] | None = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float | None = None
    top_p: float | None = None
    n: int = 1
    max_completion_tokens: int | None = None
    max_tokens: int | None = None
    stop: str | list[str] | None = None
    stream: bool = False
    stream_options: dict[str, Any] | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    logit_bias: dict[str, float] | None = None
    user: str | None = None
    functions: list[FunctionDef] | None = None
    function_call: str | dict[str, str] | None = None
    tools: list[ToolDef] | None = None
    tool_choice: str | dict[str, Any] | None = None
    response_format: ResponseFormat | None = None
    seed: int | None = None


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessage = Field(default_factory=lambda: ChatMessage(role="assistant", content=""))
    finish_reason: str | None = None
    logprobs: Any | None = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    model: str
    choices: list[ChatChoice] = Field(default_factory=list)
    usage: Usage | None = None
    system_fingerprint: str | None = None


class DeltaContent(BaseModel):
    content: str | None = None
    role: str | None = None
    function_call: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ChatStreamChoice(BaseModel):
    index: int = 0
    delta: DeltaContent = Field(default_factory=DeltaContent)
    finish_reason: str | None = None


class ChatCompletionStreamChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    model: str
    choices: list[ChatStreamChoice] = Field(default_factory=list)


# ---- Embeddings ----

class EmbeddingRequest(BaseModel):
    model: str
    input: str | list[str]
    encoding_format: Literal["float", "base64"] = "float"
    dimensions: int | None = None
    user: str | None = None


class EmbeddingData(BaseModel):
    object: str = "embedding"
    index: int = 0
    embedding: list[float] = Field(default_factory=list)


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingData] = Field(default_factory=list)
    model: str
    usage: Usage | None = None


# ---- Images ----

class ImageGenerationRequest(BaseModel):
    model: str
    prompt: str
    n: int = 1
    size: str = "1024x1024"
    response_format: Literal["url", "b64_json"] = "url"
    quality: Literal["standard", "hd"] | None = None
    style: Literal["vivid", "natural"] | None = None
    user: str | None = None


class ImageData(BaseModel):
    url: str | None = None
    b64_json: str | None = None
    revised_prompt: str | None = None


class ImageResponse(BaseModel):
    created: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    data: list[ImageData] = Field(default_factory=list)


# ---- Audio Speech ----

class SpeechRequest(BaseModel):
    model: str
    input: str
    voice: str = "alloy"
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3"
    speed: float = 1.0


# ---- Audio Transcription ----

class TranscriptionRequest(BaseModel):
    file: Any
    model: str
    language: str | None = None
    prompt: str | None = None
    response_format: str = "json"
    temperature: float = 0.0


class TranscriptionResponse(BaseModel):
    text: str


# ---- Models List ----

class ModelEntry(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    owned_by: str = "mini-litellm"


class ModelsListResponse(BaseModel):
    object: str = "list"
    data: list[ModelEntry] = Field(default_factory=list)


# ---- Error ----

class ErrorDetail(BaseModel):
    message: str
    type: str = "api_error"
    param: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
