"""Inyección de dependencias comunes para las rutas y controladores de la API."""
from app.core.database import get_db

__all__ = ["get_db"]
