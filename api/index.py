"""
Vercel serverless entrypoint for Mini LiteLLM Gateway.

Vercel looks for a top-level 'app' WSGI/ASGI variable.
"""

import sys
import os

# ---- Path: ensure modules are importable ----
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ---- Load configuration early ----
from app.config.settings import load_config, get_config
try:
    load_config()
    config = get_config()
    log_level = config.gateway.log_level
except Exception:
    log_level = "INFO"

import logging
logging.basicConfig(level=log_level)
logger = logging.getLogger("vercel")
logger.info("Mini LiteLLM Gateway starting on Vercel...")

# ---- Create FastAPI app with all routes ----
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.health_checker import health_checker

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting health checker...")
    await health_checker.start()
    yield
    await health_checker.stop()

app = FastAPI(
    title="Mini LiteLLM Gateway",
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

logger.info("All routes registered — ready to serve")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 4000))
    uvicorn.run(app, host="0.0.0.0", port=port)
