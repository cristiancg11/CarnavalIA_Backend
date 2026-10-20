"""Modelo ORM para los reportes e incidencias ciudadanas del Carnaval."""
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ReportCategory(str, Enum):
    """Categorías permitidas para los reportes de incidentes."""
    AGLOMERACION = "Aglomeracion"
    EMERGENCIA = "Emergencia"
    CALLE_BLOQUEADA = "Calle_Bloqueada"
    PERSONA_PERDIDA = "Persona_Perdida"
    OBJETO_PERDIDO = "Objeto_Perdido"
    RIESGO = "Riesgo"


class ReportStatus(str, Enum):
    """Estados del ciclo de vida de un reporte."""
    PENDIENTE = "Pendiente"
    EN_REVISION = "En_Revision"
    ATENDIDO = "Atendido"
    DESCARTADO = "Descartado"


class Report(Base):
    """Entidad de reportes de incidencias generados por ciudadanos o detectados por IA."""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default=ReportStatus.PENDIENTE.value, nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    ai_risk_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relación inversa con el usuario que creó el reporte
    user: Mapped[Optional["User"]] = relationship("User", back_populates="reports")
