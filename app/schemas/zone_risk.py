"""Esquemas Pydantic para el módulo de Zonas de Riesgo y Congestión."""
from pydantic import BaseModel, ConfigDict, Field


class ZoneRiskBase(BaseModel):
    """Esquema base para la información de riesgo y congestión de una zona."""
    zone_name: str = Field(..., description="Nombre del sector o zona de la Senda del Carnaval.")
    risk_level: str = Field(..., description="Nivel de riesgo acumulado ('Bajo', 'Medio', 'Alto').")
    congestion_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Porcentaje estimado de congestión en la zona.")
    active_reports_count: int = Field(default=0, ge=0, description="Cantidad de reportes de incidencias activos en la zona.")
    latitude: float = Field(..., description="Latitud central geográfica de la zona.")
    longitude: float = Field(..., description="Longitud central geográfica de la zona.")
    radius_meters: float = Field(..., gt=0, description="Radio de cobertura en metros para la zona.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "zone_name": "Plaza del Carnaval",
                "risk_level": "Medio",
                "active_reports_count": 3,
                "latitude": 1.2090,
                "longitude": -77.2770,
                "radius_meters": 350.0
            }
        }
    }


class ZoneRiskResponse(ZoneRiskBase):
    """Esquema de respuesta para una zona de riesgo incluyendo su identificador único."""
    id: int = Field(..., description="Identificador único numérico de la zona.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "zone_name": "Plaza del Carnaval",
                "risk_level": "Medio",
                "active_reports_count": 3,
                "latitude": 1.2090,
                "longitude": -77.2770,
                "radius_meters": 350.0
            }
        }
    )
