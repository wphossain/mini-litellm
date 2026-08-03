"""
Vercel serverless adapter.

Vercel calls this module directly instead of running Uvicorn.
The 'app' export is picked up by vercel.json -> @vercel/python.
"""

import sys
import os

# Point sys.path to the project root (parent of api/)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Import the FastAPI app from main
from main import app

# Vercel expects 'app' as the ASGI handler
