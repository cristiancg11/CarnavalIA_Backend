"""Modelo ORM para los reportes e incidencias ciudadanas del Carnaval respaldado en Supabase."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Text, Float, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ReportCategory(str, Enum):
    """Categorías permitidas para los reportes de incidentes."""
    SEGURIDAD = "seguridad"
    PRIMEROS_AUXILIOS = "primeros auxilios"
    EXTRAVIO = "extravío"
    TRAFICO = "tráfico"
    AGLOMERACION = "Aglomeracion"
    EMERGENCIA = "Emergencia"


class ReportStatus(str, Enum):
    """Estados del ciclo de vida de un reporte."""
    PENDIENTE = "Pendiente"
    EN_REVISION = "En_Revision"
    ATENDIDO = "Atendido"
    DESCARTADO = "Descartado"


class Report(Base):
    """Entidad de reportes de incidencias en la tabla limpia reports de Supabase."""
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="Pendiente", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
