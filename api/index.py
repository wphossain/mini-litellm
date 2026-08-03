"""
Vercel serverless adapter using Mangum.

FastAPI is ASGI-based, but Vercel Python Functions expect WSGI.
Mangum wraps the ASGI app into a Vercel-compatible handler.
"""

import sys
import os

# Point sys.path to the project root (parent of api/)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Import the FastAPI app from main
from main import app

from mangum import Mangum

# Create Vercel-compatible handler
handler = Mangum(app, lifespan="off")
