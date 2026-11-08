"""Punto de entrada principal para CarnavalIA API.

Sistema inteligente para el Carnaval de Negros y Blancos de Pasto.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
# Importar modelos para que Base.metadata los reconozca al crear las tablas
import app.models  # noqa: F401
# Importar script de carga inicial de datos
from app.db.seed import seed_points_of_interest
# Importar cliente resiliente de Supabase
from app.db.supabase import supabase_client
# Importar router unificado de la API v1, health, reportes, autenticación y GuaneñaBot
from app.api.v1.api import api_router
from app.api.v1.chat import router as guanena_chat_router
from app.api.health import router as health_router
from app.api.routes.reports import router as reports_router
from app.api.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: crea tablas y ejecuta seeders al iniciar."""
    # 1. Creación automática de tablas en la base de datos si no existen
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        print(f"[LIFESPAN] Advertencia al sincronizar metadatos: {exc}")

    # 2. Ejecución del seeder de puntos de interés iniciales
    try:
        with SessionLocal() as db:
            seed_points_of_interest(db)
    except Exception as exc:
        print(f"[LIFESPAN] Advertencia al ejecutar seeder inicial: {exc}")

    yield


# Instancia de FastAPI con ciclo de vida (lifespan)
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API inteligente para la gestión y experiencia interactiva del Carnaval de Negros y Blancos de Pasto.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configuración de Middleware de CORS Universal (permite todos los orígenes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers de la API
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(guanena_chat_router, prefix="/api/v1/chat")
app.include_router(health_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


@app.get("/", tags=["General"])
async def root():
    """Ruta raíz de bienvenida al sistema CarnavalIA."""
    return {
        "message": "¡Bienvenido a CarnavalIA API! Sistema inteligente para el Carnaval de Negros y Blancos de Pasto.",
        "status": "online",
        "documentation": "/docs",
        "version": settings.VERSION
    }


@app.get("/api/health/db", tags=["Health"], summary="Healthcheck profundo de Base de Datos Supabase")
async def health_check_db():
    """Sondeo rápido de conectividad hacia Supabase."""
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


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Endpoint para verificación del estado del servicio."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
