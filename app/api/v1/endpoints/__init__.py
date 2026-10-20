"""Controladores y endpoints de la API v1."""
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.points_of_interest import router as pois_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.zones import router as zones_router

__all__ = ["reports_router", "pois_router", "chat_router", "zones_router"]
