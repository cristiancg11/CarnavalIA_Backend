"""Esquemas Pydantic para la entidad Report respaldada en Supabase."""
import uuid
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReportBase(BaseModel):
    """Atributos comunes del reporte ciudadano."""
    title: str = Field(..., description="Título de la incidencia")
    category: str = Field(..., description="Categoría (seguridad, primeros auxilios, extravío, tráfico)")
    description: Optional[str] = Field(None, description="Descripción detallada de la incidencia")
    latitude: float = Field(..., description="Latitud geográfica")
    longitude: float = Field(..., description="Longitud geográfica")


class ReportCreate(BaseModel):
    """Esquema para crear un reporte ciudadano."""
    title: str = Field(..., description="Título de la incidencia")
    category: str = Field(..., description="Categoría (seguridad, primeros auxilios, extravío, tráfico)")
    description: Optional[str] = Field(None, description="Descripción del reporte")
    latitude: Optional[float] = Field(None, description="Latitud")
    longitude: Optional[float] = Field(None, description="Longitud")
    coordinates: Optional[List[float]] = Field(None, description="Coordenadas opcionales [lat, lng]")

    @model_validator(mode="after")
    def populate_coordinates(self) -> "ReportCreate":
        if self.coordinates and len(self.coordinates) >= 2:
            if self.latitude is None:
                self.latitude = float(self.coordinates[0])
            if self.longitude is None:
                self.longitude = float(self.coordinates[1])
        elif self.latitude is None or self.longitude is None:
            self.latitude = 1.2136
            self.longitude = -77.2811
        return self


class ReportResponse(BaseModel):
    """Esquema de respuesta con datos del reporte de Supabase."""
    id: Union[uuid.UUID, str]
    title: str
    category: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    status: Optional[str] = "Pendiente"
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
