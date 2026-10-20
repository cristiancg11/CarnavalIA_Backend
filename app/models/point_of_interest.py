"""Modelo ORM para Puntos de Interés (POI) en la ruta del Carnaval."""
from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class POICategory(str, Enum):
    """Categorías de servicios y puntos clave durante el evento."""
    SALUD = "Salud"
    POLICIA = "Policia"
    BANIO = "Banio"
    TARIMA = "Tarima"
    SALIDA = "Salida"


class PointOfInterest(Base):
    """Entidad de puntos de interés y servicios en el sendero del Carnaval."""
    __tablename__ = "points_of_interest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
