"""API routers for the Split Bill application"""

from .health import router as health_router
from .ocr import router as ocr_router

__all__ = [
    "health_router",
    "ocr_router"
]