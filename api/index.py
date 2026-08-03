"""
Vercel serverless entrypoint for Mini LiteLLM Gateway.

Vercel's Python runtime imports this file and looks for a top-level 'app'
variable that is a WSGI/ASGI application. This module creates the FastAPI
application directly to avoid cross-module import issues on Vercel.

On Vercel, we cannot rely on config.yaml. Instead, all configuration
comes from environment variables (set in Vercel dashboard).
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

# ---- Lazy-load config & create app ----
# We import inside the lifespan to avoid import errors at module level

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

app = FastAPI(
    title="Mini LiteLLM Gateway (Vercel)",
    description="Lightweight OpenAI-compatible AI Gateway",
    version="1.0.0",
    docs_url="/docs",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Import and register routes ----
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

logger.info("All routes registered on Vercel")

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
