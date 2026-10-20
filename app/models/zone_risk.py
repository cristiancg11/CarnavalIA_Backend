"""Modelo ORM para monitoreo y análisis de riesgo en zonas del Carnaval."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Integer, String, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RiskLevel(str, Enum):
    """Niveles de riesgo clasificados para una zona."""
    BAJO = "Bajo"
    MEDIO = "Medio"
    ALTO = "Alto"


class ZoneRisk(Base):
    """Entidad para almacenar el estado de congestión y nivel de riesgo de cada sector."""
    __tablename__ = "zone_risk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    zone_name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    congestion_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default=RiskLevel.BAJO.value, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
