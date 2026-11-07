"""Modelo ORM para los eventos oficiales del Carnaval de Negros y Blancos."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Event(Base):
    """Entidad de eventos oficiales y programación del Carnaval de Pasto."""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_label: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    start_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    end_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="Desfile", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

