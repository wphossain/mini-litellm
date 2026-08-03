"""
Mini LiteLLM Gateway — FastAPI Entrypoint.

Lightweight AI Gateway using LiteLLM SDK (NOT Proxy).
Optimized for <150MB idle RAM.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.audio import router as audio_router
from app.api.chat import router as chat_router
from app.api.embeddings import router as embeddings_router
from app.api.health import router as health_router
from app.api.images import router as images_router
from app.api.models import router as models_router
from app.config.settings import get_config, load_config
from app.core.health_checker import health_checker

logging.basicConfig(
    level=os.environ.get("GATEWAY_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gateway")

# ---- CORS middleware must be added BEFORE lifespan starts ----
_config_loaded = False


def _ensure_config() -> None:
    global _config_loaded
    if not _config_loaded:
        try:
            load_config()
            _config_loaded = True
        except Exception as e:
            logger.warning("Config load deferred: %s", e)


_ensure_config()
config = get_config()

# ---- Create app ----
app = FastAPI(
    title="Mini LiteLLM Gateway",
    description="Lightweight OpenAI-compatible AI Gateway using LiteLLM SDK",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---- CORS (MUST be before lifespan, before routes) ----
if config.cors.enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )
    logger.info("CORS enabled")


# ---- Lifespan (startup/shutdown) ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 48)
    logger.info("  Mini LiteLLM Gateway v%s", config.gateway.version)
    logger.info("  Providers: %d enabled / %d total",
                sum(1 for p in config.providers if p.enabled),
                len(config.providers))
    logger.info("  Auth: %s", "DISABLED" if config.auth.disabled else "ENABLED")
    logger.info("=" * 48)

    await health_checker.start()
    yield
    await health_checker.stop()
    logger.info("Gateway stopped")


# ---- Routes ----
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(models_router)
app.include_router(embeddings_router)
app.include_router(images_router)
app.include_router(audio_router)
app.include_router(admin_router)

logger.info("All routes registered")


# ---- Local dev ----
if __name__ == "__main__":
    import uvicorn
    host = config.gateway.host
    port = int(os.environ.get("PORT", config.gateway.port))
    uvicorn.run("main:app", host=host, port=port, log_level="info", access_log=True)
