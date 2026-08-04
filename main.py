"""
Mini LiteLLM Gateway — FastAPI Entrypoint with Dashboard Static Mounting.

Lightweight AI Gateway using LiteLLM SDK (NOT Proxy).
Optimized for <150MB idle RAM.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

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

# ---- Config setup ----
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

# ---- App ----
app = FastAPI(
    title="Mini LiteLLM Gateway",
    description="Lightweight OpenAI-compatible AI Gateway using LiteLLM SDK",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---- CORS ----
if config.cors.enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )
    logger.info("CORS enabled")


# ---- Lifespan ----
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


app.router.lifespan_context = lifespan

# ---- Routes ----
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(models_router)
app.include_router(embeddings_router)
app.include_router(images_router)
app.include_router(audio_router)
app.include_router(admin_router)

# ---- Dashboard Static Files Mounting ----
# Serves React app at /admin/ui and redirects / -> /admin/ui
dashboard_dist = Path("/app/dashboard/dist")
if not dashboard_dist.exists():
    dashboard_dist = Path("./dashboard/dist")

if dashboard_dist.exists():
    logger.info("Mounting Admin Dashboard from %s", dashboard_dist)
    app.mount("/admin/ui", StaticFiles(directory=str(dashboard_dist), html=True), name="dashboard")

    # Serve index.html for SPA routing (React Router)
    @app.get("/admin/ui/{full_path:path}")
    async def serve_spa(full_path: str):
        target = dashboard_dist / full_path
        if target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(dashboard_dist / "index.html")

    # Redirect root / to /admin/ui for browser convenience
    @app.get("/", include_in_schema=False)
    async def redirect_to_ui():
        return RedirectResponse(url="/admin/ui/")
else:
    logger.info("Dashboard build not found at %s — serving API health on root", dashboard_dist)

logger.info("All routes registered")

# ---- Local dev ----
if __name__ == "__main__":
    import uvicorn
    host = config.gateway.host
    port = int(os.environ.get("PORT", config.gateway.port))
    uvicorn.run("main:app", host=host, port=port, log_level="info", access_log=True)
