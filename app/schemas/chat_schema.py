"""Esquemas Pydantic para el motor conversacional inteligente GuaneñaBot."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Solicitud de consulta conversacional enviada por el turista/ciudadano."""
    message: str = Field(..., min_length=1, description="Mensaje o pregunta en lenguaje natural.")
    user_lat: Optional[float] = Field(None, description="Latitud geográfica actual del usuario.")
    user_lng: Optional[float] = Field(None, description="Longitud geográfica actual del usuario.")


class MapAction(BaseModel):
    """Acción estructurada determinista para interactuar con el mapa de Pasto."""
    action_type: str = Field(
        ...,
        description="Tipo de acción: 'ROUTE_TO_EVENT_START', 'SHOW_SENDA', 'FILTER_POIS', 'INFO_ONLY'"
    )
    target_name: Optional[str] = Field(None, description="Nombre descriptivo del hito o destino.")
    target_coords: Optional[List[float]] = Field(None, description="Coordenadas geográficas [lat, lng].")
    event_date: Optional[str] = Field(None, description="Identificador de fecha del Carnaval (ej. 'jan_04').")
    category: Optional[str] = Field(None, description="Categoría asociada al hito o servicio.")


class ChatResponse(BaseModel):
    """Respuesta cultural estructurada devuelta por GuaneñaBot."""
    reply: str = Field(..., description="Respuesta cordial con calidez pastusa e información cultural.")
    map_action: Optional[MapAction] = Field(None, description="Acción sugerida para enfocar o rutear en el mapa.")
