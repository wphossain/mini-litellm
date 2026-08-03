"""POST /v1/chat/completions and /v1/responses endpoints."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.auth import require_auth
from app.core.rate_limiter import check_rate_limit
from app.models.openai_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChunk,
    ErrorResponse,
    ErrorDetail,
)
from app.services.gateway_service import gateway_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/v1/chat/completions",
    response_model=None,
    summary="Create a chat completion",
    tags=["Chat"],
)
async def chat_completions(request: Request, body: ChatCompletionRequest):
    await check_rate_limit(request)
    _, tier = await require_auth(request)

    try:
        if body.stream:
            return StreamingResponse(
                _stream_chat(body, request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        client_ip = request.client.host if request.client else None
        result: ChatCompletionResponse = await gateway_service.chat_completion(body, client_ip)
        return result.model_dump(exclude_none=True)

    except Exception as e:
        logger.error("Chat completion failed: %s", str(e))
        error_msg = str(e)
        status = 500
        if "429" in error_msg or "rate" in error_msg.lower():
            status = 429
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            status = 401
        if "not found" in error_msg.lower():
            status = 404
        raise HTTPException(
            status_code=status,
            detail={"error": {"message": error_msg[:500], "type": "api_error"}},
        )


async def _stream_chat(body: ChatCompletionRequest, request: Request):
    try:
        client_ip = request.client.host if request.client else None
        async for chunk in gateway_service.chat_completion_stream(body, client_ip):
            yield f"data: {json.dumps(chunk.model_dump(exclude_none=True))}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error("Stream chat failed: %s", str(e))
        error_chunk = json.dumps({
            "error": {"message": str(e)[:500], "type": "api_error"}
        })
        yield f"data: {error_chunk}\n\n"
        yield "data: [DONE]\n\n"


@router.post(
    "/v1/responses",
    summary="Create a response (OpenAI Responses API compatibility)",
    tags=["Chat"],
)
async def responses_endpoint(request: Request, body: ChatCompletionRequest):
    """Forward /v1/responses to /v1/chat/completions for compatibility."""
    return await chat_completions(request, body)
