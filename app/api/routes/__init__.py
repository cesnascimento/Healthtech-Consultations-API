"""API route modules."""

from app.api.routes.consultations import router as consultations_router
from app.api.routes.health import router as health_router

__all__ = ["consultations_router", "health_router"]
