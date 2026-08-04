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
from fastapi.responses import FileResponse

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

# ---- Config ----
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

# ---- Lifespan ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    await health_checker.start()
    yield
    await health_checker.stop()

app.router.lifespan_context = lifespan

# ---- API Routes (MUST COME BEFORE STATIC FILES) ----
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(models_router)
app.include_router(embeddings_router)
app.include_router(images_router)
app.include_router(audio_router)
app.include_router(admin_router)

# ---- Dashboard Static Files ----
_base_dir = Path(__file__).parent.resolve()
candidates = [
    _base_dir / "dashboard" / "dist",
    Path("/app/dashboard/dist"),
]

dashboard_dist = None
for c in candidates:
    if c.exists() and (c / "index.html").exists():
        dashboard_dist = c
        break

if dashboard_dist:
    logger.info("Serving Admin Dashboard from: %s", dashboard_dist)
    
    # Serve the static files (CSS, JS, etc.)
    # We mount at root / but this must stay AFTER api routes
    app.mount("/assets", StaticFiles(directory=str(dashboard_dist / "assets")), name="assets")

    # Serve index.html for root and any other non-API routes (SPA support)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_dashboard(full_path: str):
        # If it looks like an API call or internal file, let it fall through
        if full_path.startswith(("v1/", "admin/", "health", "docs", "redoc", "openapi")):
            # This shouldn't normally be hit if routes match correctly, but just in case
            return {"error": "Not Found", "path": full_path}
        
        # Check if specific file exists in dist (for icons, robots.txt, etc.)
        file_path = dashboard_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
            
        # Fallback to index.html for React Router
        return FileResponse(dashboard_dist / "index.html")
else:
    logger.error("Dashboard NOT FOUND. Tried: %s", [str(c) for c in candidates])
    @app.get("/", include_in_schema=False)
    async def fallback_root():
        return {"status": "ok", "message": "Gateway API is live. Dashboard build missing."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.gateway.host, port=int(os.environ.get("PORT", config.gateway.port)), log_level="info")
