"""GET /v1/models endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from app.core.auth import require_auth
from app.services.gateway_service import gateway_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/v1/models",
    summary="List all available models",
    tags=["Models"],
)
async def list_models(request: Request):
    await require_auth(request)
    result = await gateway_service.list_models()
    return result.model_dump(exclude_none=True)
