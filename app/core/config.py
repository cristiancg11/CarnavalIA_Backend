"""Módulo de configuración centralizada y variables de entorno para CarnavalIA API.

Realiza validación estricta con Pydantic Settings para garantizar que
todas las credenciales requeridas (Supabase, Gemini, CORS) estén presentes
y bien formadas antes de iniciar cualquier componente del sistema.
"""
import json
import sys
from pathlib import Path
from typing import List, Union
from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración central de la aplicación con validación estricta de entorno."""
    PROJECT_NAME: str = "CarnavalIA API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS: Orígenes permitidos (por defecto incluye variantes locales de Vite y producción)
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    # Base de datos relacional (PostgreSQL / Pooler de Supabase)
    DATABASE_URL: str = "postgresql://postgres.weacieobzyzkmmlwydbs:SecurePass12##@aws-0-ca-central-1.pooler.supabase.com:6543/postgres"

    # Conexión directa / cliente de Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Inteligencia Artificial (Google Gemini) para el motor de GuaneñaBot
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.5-flash"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Asegura el formato lista para CORS_ORIGINS e incluye orígenes de desarrollo frontend."""
        origins: List[str] = []
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    origins = json.loads(v_stripped)
                except Exception:
                    origins = [item.strip().strip("'\"") for item in v_stripped[1:-1].split(",") if item.strip()]
            else:
                origins = [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            origins = list(v)

        # Garantizar que las variantes locales de Vite estén presentes
        default_local = ["http://localhost:5173", "http://127.0.0.1:5173"]
        for local_origin in default_local:
            if local_origin not in origins and "*" not in origins:
                origins.append(local_origin)

        return origins if origins else ["*"]

    @field_validator("SUPABASE_URL")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        """Valida que SUPABASE_URL esté presente y tenga formato de URL HTTPS/HTTP."""
        val = v.strip() if v else ""
        if not val or val == "tu_supabase_url_aqui":
            raise ValueError(
                "[ERROR CRÍTICO DE ENTORNO] Variable obligatoria 'SUPABASE_URL' no configurada o vacía en .env. "
                "Debe proporcionar una URL válida de Supabase (ej: https://<project-ref>.supabase.co)."
            )
        if not (val.startswith("http://") or val.startswith("https://")):
            raise ValueError(
                f"[ERROR CRÍTICO DE ENTORNO] 'SUPABASE_URL' inválida: '{val}'. "
                "Debe iniciar con 'https://' o 'http://'."
            )
        return val

    @field_validator("SUPABASE_KEY")
    @classmethod
    def validate_supabase_key(cls, v: str) -> str:
        """Valida que SUPABASE_KEY esté configurada (anon o service_role)."""
        val = v.strip() if v else ""
        if not val or val == "tu_clave_de_supabase_anon_o_service_role":
            raise ValueError(
                "[ERROR CRÍTICO DE ENTORNO] Variable obligatoria 'SUPABASE_KEY' no configurada o vacía en .env. "
                "Debe proporcionar una clave anon o service_role válida de Supabase."
            )
        return val

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def validate_gemini_api_key(cls, v: str) -> str:
        """Valida que GEMINI_API_KEY esté configurada para GuaneñaBot."""
        val = v.strip() if v else ""
        if not val or val == "tu_clave_de_gemini_aqui":
            raise ValueError(
                "[ERROR CRÍTICO DE ENTORNO] Variable obligatoria 'GEMINI_API_KEY' no configurada o vacía en .env. "
                "Se requiere para el motor de conversación cultural de GuaneñaBot."
            )
        return val

    model_config = SettingsConfigDict(
        env_file=(str(Path(__file__).resolve().parent.parent.parent / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


def load_settings() -> Settings:
    """Carga y valida estrictamente las variables de entorno."""
    try:
        return Settings()
    except ValidationError as exc:
        print("\n" + "!" * 80, file=sys.stderr)
        print("ERROR AL CARGAR VARIABLES DE ENTORNO (CarnavalIA API):", file=sys.stderr)
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err["loc"])
            print(f"  - Campo '{loc}': {err['msg']}", file=sys.stderr)
        print("!" * 80 + "\n", file=sys.stderr)
        raise exc


# Instancia singleton accesible en toda la aplicación
settings = load_settings()
