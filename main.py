"""
Mini LiteLLM Gateway — FastAPI Entrypoint.

Lightweight AI Gateway using LiteLLM SDK (NOT Proxy).
Optimized for <150MB idle RAM on Northflank Free / Render Free / Railway / VPS.
"""

from __future__ import annotations

import logging
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
from app.config.settings import load_config, get_config
from app.core.health_checker import health_checker

# ---- Logging ----

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gateway")

# ---- Lifecycle ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    logger.info("═══════════════════════════════════════")
    logger.info("  Mini LiteLLM Gateway — Starting...")
    logger.info("═══════════════════════════════════════")

    try:
        config = load_config()
        logger.info("Version: %s", config.gateway.version)
        logger.info("Host: %s:%d", config.gateway.host, config.gateway.port)
        logger.info("Providers: %d (%d enabled)", len(config.providers), sum(1 for p in config.providers if p.enabled))
        logger.info("Aliases: %d", len(config.model_aliases))
        logger.info("Auth: %s", "DISABLED" if config.auth.disabled else "ENABLED")
    except Exception as e:
        logger.error("Failed to load configuration: %s", e)
        raise

    await health_checker.start()
    logger.info("Gateway is ready to accept requests")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await health_checker.stop()
    logger.info("Gateway stopped")


# ---- FastAPI App ----

app = FastAPI(
    title="Mini LiteLLM Gateway",
    description="Lightweight OpenAI-compatible AI Gateway using LiteLLM SDK",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ---- CORS Middleware ----

def _setup_cors(app: FastAPI) -> None:
    config = get_config()
    if not config.cors.enabled:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )
    logger.info("CORS enabled for %d origins", len(config.cors.allow_origins))


# ---- Register Routes ----

# Health first — no auth required
app.include_router(health_router)

# OpenAI-compatible endpoints
app.include_router(chat_router)
app.include_router(models_router)
app.include_router(embeddings_router)
app.include_router(images_router)
app.include_router(audio_router)

# Admin API (auth enforced internally)
app.include_router(admin_router)

logger.info("All routes registered")


# ---- Setup CORS after config is loaded ----
try:
    _setup_cors(app)
except Exception:
    logger.warning("CORS setup deferred — config not yet loaded")


# ---- Convenience — Uvicorn runner ----
if __name__ == "__main__":
    import uvicorn

    try:
        config = load_config()
        host = config.gateway.host
        port = config.gateway.port
        log_level = config.gateway.log_level.lower()
    except Exception:
        host = "0.0.0.0"
        port = 4000
        log_level = "info"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        access_log=True,
    )
