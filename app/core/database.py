"""Configuración del motor de Base de Datos y Sesiones de SQLAlchemy."""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# Normalización y compatibilidad de drivers de BD
db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif db_url.startswith("postgresql://"):
    # En Windows, psycopg2 puede ser bloqueado por directivas de seguridad/AppLocker.
    # pg8000 es 100% puro Python y no requiere DLLs compiladas externas.
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)

# Creación del engine
engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True
)

# Fábrica de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Clase base para todos los modelos ORM (SQLAlchemy 2.0)
class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    """Función generadora para inyección de dependencia de sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
