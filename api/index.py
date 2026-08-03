"""
Vercel serverless adapter.

Vercel calls this module directly instead of running Uvicorn.
"""

import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vercel")

# Point sys.path to the project root (parent of api/ directory)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Also ensure the parent works for relative imports
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

logger.info("Vercel adapter starting...")
logger.info("sys.path: %s", sys.path)
logger.info("CWD: %s", os.getcwd())
logger.info("Root: %s", _project_root)

# List files in root for debugging
for f in os.listdir(_project_root):
    logger.info("  root file: %s", f)

# Import the FastAPI app from main
try:
    from main import app
    logger.info("FastAPI app loaded successfully")
except Exception as e:
    logger.error("Failed to import main: %s", e)
    import traceback
    logger.error(traceback.format_exc())
    raise
