"""Endpoints para verificación de salud y conectividad de base de datos."""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.db.supabase import supabase_client

router = APIRouter(tags=["Health"])


@router.get(
    "/health/db",
    summary="Healthcheck de Base de Datos Supabase",
    description="Ejecuta una consulta de sondeo rápida a Supabase (tablas reports/events)."
)
async def check_db_health():
    """Consulta de sondeo activa a Supabase."""
    health_result = supabase_client.check_connection()
    if health_result.get("status") == "ok":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "database": "connected",
                "provider": "supabase"
            }
        )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "error",
            "message": "Supabase unreachable"
        }
    )
