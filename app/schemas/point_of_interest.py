"""Esquemas Pydantic para Puntos de Interés (POI) del Carnaval."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class POIBase(BaseModel):
    """Esquema base para puntos de interés."""
    name: str = Field(..., min_length=2, max_length=150, description="Nombre del punto de interés")
    category: str = Field(
        ...,
        description="Categoría del punto de interés: Salud, Policia, Banio, Tarima, Salida"
    )
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Coordenada de latitud en Pasto")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Coordenada de longitud en Pasto")
    description: Optional[str] = Field(None, description="Descripción o detalles adicionales del punto")


class POICreate(POIBase):
    """Esquema para la creación de un nuevo punto de interés."""
    pass


class POIResponse(POIBase):
    """Esquema de respuesta tras consultar o registrar un punto de interés."""
    id: int

    model_config = ConfigDict(from_attributes=True)
