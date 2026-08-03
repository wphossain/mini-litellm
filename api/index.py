"""
Vercel serverless entrypoint for Mini LiteLLM Gateway.

Vercel's Python runtime looks for a top-level 'app' variable.
This module creates the FastAPI application directly to avoid
cross-module import issues on Vercel serverless.

On Vercel, config comes from environment variables (set in dashboard).
"""

import sys
import os
import logging

# ---- Path Setup ----
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
for p in [_project_root]:
    if p not in sys.path:
        sys.path.insert(0, p)
os.chdir(_project_root)

# ---- Logging ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vercel")

# ---- Ensure config is loaded before routes are hit ----
from app.config.settings import load_config
try:
    load_config()
    cfg = load_config()
    logger.info("Config loaded: %d providers", len(cfg.providers))
except Exception as e:
    logger.warning("Config load issue: %s", e)

# ---- FastAPI App ----
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.health_checker import health_checker

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Vercel gateway starting...")
    await health_checker.start()
    yield
    await health_checker.stop()

app = FastAPI(
    title="Mini LiteLLM Gateway (Vercel)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Import and register all routes ----
from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.chat import router as chat_router
from app.api.embeddings import router as embeddings_router
from app.api.images import router as images_router
from app.api.audio import router as audio_router
from app.api.admin import router as admin_router

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(models_router)
app.include_router(embeddings_router)
app.include_router(images_router)
app.include_router(audio_router)
app.include_router(admin_router)

logger.info("All routes registered")

# For local testing
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "4000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
