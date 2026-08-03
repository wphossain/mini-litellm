"""POST /v1/audio/speech and /v1/audio/transcriptions endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from app.core.auth import require_auth
from app.core.rate_limiter import check_rate_limit
from app.models.openai_models import SpeechRequest, TranscriptionRequest, TranscriptionResponse
from app.services.gateway_service import gateway_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/v1/audio/speech",
    summary="Generate speech from text",
    tags=["Audio"],
)
async def create_speech(request: Request, body: SpeechRequest):
    await check_rate_limit(request)
    await require_auth(request)

    try:
        audio_bytes = await gateway_service.create_speech(body)
        content_type = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac",
            "wav": "audio/wav",
            "pcm": "audio/pcm",
        }.get(body.response_format, "audio/mpeg")

        return Response(content=audio_bytes, media_type=content_type)
    except Exception as e:
        logger.error("Speech generation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": str(e)[:500], "type": "api_error"}},
        )


@router.post(
    "/v1/audio/transcriptions",
    summary="Transcribe audio to text",
    tags=["Audio"],
)
async def create_transcription(
    request: Request,
    file: UploadFile,
    model: str = Form(...),
    language: str | None = Form(None),
    prompt: str | None = Form(None),
    response_format: str = Form("json"),
    temperature: float = Form(0.0),
):
    await check_rate_limit(request)
    await require_auth(request)

    try:
        file_content = await file.read()
        trans_request = TranscriptionRequest(
            file=file_content,
            model=model,
            language=language,
            prompt=prompt,
            response_format=response_format,
            temperature=temperature,
        )
        result = await gateway_service.create_transcription(trans_request)
        return result.model_dump(exclude_none=True)
    except Exception as e:
        logger.error("Transcription failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": str(e)[:500], "type": "api_error"}},
        )
