"""
Vercel serverless entrypoint.

Minimal import — must work on Vercel's Python 3.12 serverless runtime.
"""

import sys
import os

# Add project root to sys.path so 'app.*' imports work
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

# FastAPI + CORS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the application
app = FastAPI(title="Mini LiteLLM Gateway", version="1.0.0", docs_url="/docs")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Root health endpoint (no deps)
@app.get("/")
@app.get("/health")
async def root_health():
    return {"status": "ok", "service": "Mini LiteLLM Gateway", "version": "1.0.0"}

@app.get("/health/readiness")
async def readiness():
    return {"status": "ready"}

@app.get("/health/liveness")
async def liveness():
    return {"status": "alive"}

# ---- Try to import the full application modules ----
_import_failed = False
try:
    from app.config.settings import load_config, get_config
    load_config()
    
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
    
    print("All routes loaded successfully", flush=True)
except Exception as e:
    _import_failed = True
    print(f"Import warning (non-fatal): {e}", flush=True)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 4000))
    uvicorn.run(app, host="0.0.0.0", port=port)
