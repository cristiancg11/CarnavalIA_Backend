"""Módulo de configuración centralizada y variables de entorno."""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CarnavalIA API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]

    # Base de datos: SQLite por defecto para desarrollo local, Postgres en producción
    DATABASE_URL: str = "sqlite:///./carnavalia.db"

    # Inteligencia Artificial (Google Gemini)
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=(str(Path(__file__).resolve().parent.parent.parent / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
