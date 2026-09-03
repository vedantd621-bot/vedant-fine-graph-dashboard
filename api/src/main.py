"""
FinGraph API Compatibility Entrypoint.
Imports FastAPI app from backend.app.main to support `uvicorn api.src.main:app`.
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.main import app

__all__ = ["app"]
