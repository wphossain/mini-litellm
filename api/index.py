"""
Vercel serverless adapter.

Vercel calls this module directly instead of running Uvicorn.
The 'app' export is picked up by vercel.json -> @vercel/python.
"""

import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app from main
from main import app

# Vercel expects 'app' as the WSGI/ASGI handler
# FastAPI/Starlette ASGI apps work natively with @vercel/python
