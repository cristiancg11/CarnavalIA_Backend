"""Esquemas Pydantic para la entidad Report (Incidencias ciudadanas)."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    """Atributos comunes del reporte ciudadano."""
    title: str = Field(..., min_length=3, max_length=150, description="Título breve del reporte")
    description: Optional[str] = Field(None, description="Detalles adicionales sobre lo ocurrido")
    category: str = Field(..., description="Categoría (Aglomeracion, Emergencia, Calle_Bloqueada, Persona_Perdida, Objeto_Perdido, Riesgo)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitud geográfica en Pasto")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitud geográfica en Pasto")


class ReportCreate(ReportBase):
    """Esquema para creación de un nuevo reporte."""
    pass


class ReportResponse(ReportBase):
    """Esquema de salida tras consultar o registrar un reporte."""
    id: int
    status: str
    ai_risk_level: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
