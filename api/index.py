"""
Vercel serverless adapter for Mini LiteLLM Gateway.

Vercel calls this module directly and expects a top-level "app" variable
that is a FastAPI/ASGI application.

This file handles the full setup so Vercel can find everything.
"""

import sys
import os

# ---- Path Setup: ensure all modules are importable ----

# The api/ directory is one level below project root
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)

# Add both to sys.path so 'from app import ...' and 'from main import app' work
for p in [_project_root, _this_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Change working directory to project root so config.yaml can be found
os.chdir(_project_root)

# ---- Import the actual FastAPI application ----
# Vercel expects 'app' at module level as the ASGI handler

from main import app

# The 'app' variable is now available at module level for Vercel
