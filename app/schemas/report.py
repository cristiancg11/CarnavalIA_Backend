"""Esquemas Pydantic para la entidad Report (Incidencias ciudadanas y seguridad)."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReportBase(BaseModel):
    """Atributos base para la gestión de incidencias ciudadanas."""
    title: str = Field(..., min_length=3, max_length=150, description="Título descriptivo del reporte")
    category: str = Field(
        ...,
        description="Categoría del incidente (seguridad, primeros auxilios, extravío, tráfico, aglomeración, etc.)"
    )
    description: Optional[str] = Field(None, description="Detalles adicionales sobre lo ocurrido")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitud geográfica en Pasto")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitud geográfica en Pasto")
    coordinates: Optional[List[float]] = Field(
        None,
        description="Par de coordenadas [latitud, longitud] para frontend/mapas"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Marca de tiempo en que ocurrió el reporte"
    )

    @model_validator(mode="after")
    def unify_coordinates(self) -> "ReportBase":
        """Sincroniza el par [lat, lng] con los campos individuales de latitud y longitud."""
        if self.coordinates and len(self.coordinates) >= 2:
            if self.latitude is None:
                self.latitude = float(self.coordinates[0])
            if self.longitude is None:
                self.longitude = float(self.coordinates[1])
        elif self.latitude is not None and self.longitude is not None:
            if self.coordinates is None:
                self.coordinates = [self.latitude, self.longitude]
        else:
            # Coordenadas por defecto en el centro histórico de San Juan de Pasto (Plaza del Carnaval)
            self.latitude = 1.2136
            self.longitude = -77.2811
            self.coordinates = [1.2136, -77.2811]
        return self


class ReportCreate(ReportBase):
    """Esquema de entrada para registrar un nuevo reporte en Supabase."""
    pass


class ReportResponse(ReportBase):
    """Esquema de salida con datos confirmados del reporte."""
    id: int
    status: str = Field("Pendiente", description="Estado del reporte (Pendiente, En_Revision, Atendido, Descartado)")
    ai_risk_level: Optional[str] = Field(None, description="Nivel de riesgo clasificado por IA")
    created_at: datetime
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
