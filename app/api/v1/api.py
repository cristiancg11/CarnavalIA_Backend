"""Router unificado de la API versión 1."""
from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.points_of_interest import router as pois_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.zones import router as zones_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reportes"])
api_router.include_router(pois_router, prefix="/points-of-interest", tags=["Puntos de Interés"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chatbot IA"])
api_router.include_router(zones_router, prefix="/zones", tags=["Zonas de Riesgo"])
