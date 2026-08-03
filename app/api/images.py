"""POST /v1/images/generations endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.core.auth import require_auth
from app.core.rate_limiter import check_rate_limit
from app.models.openai_models import ImageGenerationRequest, ImageResponse
from app.services.gateway_service import gateway_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/v1/images/generations",
    response_model=None,
    summary="Generate images",
    tags=["Images"],
)
async def generate_image(request: Request, body: ImageGenerationRequest):
    await check_rate_limit(request)
    await require_auth(request)

    try:
        result: ImageResponse = await gateway_service.generate_image(body)
        return result.model_dump(exclude_none=True)
    except Exception as e:
        logger.error("Image generation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": str(e)[:500], "type": "api_error"}},
        )
