"""POST /v1/embeddings endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.core.auth import require_auth
from app.core.rate_limiter import check_rate_limit
from app.models.openai_models import EmbeddingRequest, EmbeddingResponse
from app.services.gateway_service import gateway_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/v1/embeddings",
    response_model=None,
    summary="Create embeddings",
    tags=["Embeddings"],
)
async def create_embedding(request: Request, body: EmbeddingRequest):
    await check_rate_limit(request)
    await require_auth(request)

    try:
        client_ip = request.client.host if request.client else None
        result: EmbeddingResponse = await gateway_service.create_embedding(body, client_ip)
        return result.model_dump(exclude_none=True)
    except Exception as e:
        logger.error("Embedding failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": str(e)[:500], "type": "api_error"}},
        )
