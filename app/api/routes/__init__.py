"""Módulo de rutas de la API de CarnavalIA."""
from app.api.routes.reports import router as reports_router
from app.api.routes.auth import router as auth_router

__all__ = ["reports_router", "auth_router"]
