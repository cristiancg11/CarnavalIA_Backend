"""Cliente resiliente de Supabase con manejo de reconexiones y logging estructurado.

Proporciona un wrapper robusto sobre create_client con tolerancia a fallos,
reintentos automáticos, auditoría de eventos de red y fallback de alta disponibilidad.
"""
import logging
import time
from typing import Any, Dict, List, Optional
from app.core.config import settings

# Configuración de logger estructurado para el servicio de base de datos Supabase
logger = logging.getLogger("app.db.supabase")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [SUPABASE_CLIENT] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ResilientSupabaseClient:
    """Wrapper resiliente sobre el SDK de Supabase con reconexión y fallback."""

    def __init__(self, url: str, key: str, max_retries: int = 3, retry_delay: float = 1.0):
        self.url = url
        self.key = key
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._raw_client: Optional[Any] = None
        self._is_available: bool = False
        self.init_client()

    def init_client(self) -> bool:
        """Inicializa el cliente de Supabase dentro de un bloque controlado."""
        attempt = 0
        while attempt < self.max_retries:
            attempt += 1
            logger.info(
                f"Intento de conexión a Supabase ({attempt}/{self.max_retries}) | Target: {self.url}"
            )
            try:
                from supabase import create_client, ClientOptions

                # Intentar creación con timeout controlado
                self._raw_client = create_client(self.url, self.key)
                self._is_available = True
                logger.info(
                    f"Cliente Supabase instanciado correctamente | Estado: DISPONIBLE | Intento: {attempt}"
                )
                return True
            except ImportError:
                logger.error(
                    "Módulo 'supabase' no encontrado. Instale la dependencia con 'pip install supabase'."
                )
                self._is_available = False
                return False
            except Exception as exc:
                self._is_available = False
                logger.warning(
                    f"Fallo en intento {attempt}/{self.max_retries} al inicializar Supabase: {type(exc).__name__}: {str(exc)}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        logger.error(
            "No fue posible establecer conexión directa con el cliente Supabase tras reintentos. "
            "Activando modo de resiliencia con fallback a pooler PostgreSQL."
        )
        return False

    @property
    def is_available(self) -> bool:
        """Indica si el cliente de Supabase se encuentra activo y disponible."""
        return self._is_available and self._raw_client is not None

    @property
    def client(self) -> Any:
        """Retorna la instancia interna del cliente, reintentando si fue desconectado."""
        if not self._raw_client:
            self.init_client()
        return self._raw_client

    def table(self, table_name: str) -> Any:
        """Acceso a una tabla de Supabase a través del cliente REST."""
        if not self._raw_client:
            self.init_client()
        if self._raw_client:
            return self._raw_client.table(table_name)
        raise RuntimeError("Cliente Supabase no disponible para operaciones de tabla REST.")

    def check_connection(self) -> Dict[str, Any]:
        """Ejecuta una verificación de disponibilidad y sondeo en vivo."""
        logger.info("Ejecutando sondeo de conectividad con Supabase...")
        # 1. Intentar sondeo a través del cliente REST
        if self.is_available:
            try:
                res = self._raw_client.table("reports").select("id").limit(1).execute()
                logger.info("Sondeo REST a tabla 'reports' exitoso.")
                return {
                    "status": "ok",
                    "database": "connected",
                    "provider": "supabase",
                    "protocol": "rest",
                    "details": "Conexión REST activa y respondiendo"
                }
            except Exception as rest_err:
                logger.warning(
                    f"Sondeo REST no respondió ({type(rest_err).__name__}). Probando conexión vía pooler relacional..."
                )

        # 2. Fallback resiliente: conexión relacional directa vía SQLAlchemy / PostgreSQL
        try:
            from sqlalchemy import text
            from app.core.database import engine

            with engine.connect() as conn:
                db_name = conn.execute(text("SELECT current_database();")).scalar()
                count = conn.execute(text("SELECT count(*) FROM reports;")).scalar()
                logger.info(f"Sondeo relacional PostgreSQL exitoso | DB: {db_name} | Reportes: {count}")
                return {
                    "status": "ok",
                    "database": "connected",
                    "provider": "supabase",
                    "protocol": "postgres-pooler",
                    "details": f"Conexión PostgreSQL de Supabase activa ({count} reportes registrados)"
                }
        except Exception as sql_err:
            logger.error(f"Fallo crítico: Supabase inalcanzable por REST y PostgreSQL: {sql_err}")
            return {
                "status": "error",
                "message": "Supabase unreachable",
                "error_details": str(sql_err)
            }


# Instancia singleton del cliente resiliente
supabase_resilient_wrapper = ResilientSupabaseClient(
    url=settings.SUPABASE_URL,
    key=settings.SUPABASE_KEY
)

# Alias para compatibilidad de importación
supabase = supabase_resilient_wrapper.client
supabase_client = supabase_resilient_wrapper


def get_supabase_client() -> ResilientSupabaseClient:
    """Función de conveniencia para inyección de dependencia o acceso directo."""
    return supabase_resilient_wrapper

