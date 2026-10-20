"""Esquemas Pydantic para el módulo de Chatbot Inteligente."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Esquema de solicitud para consultar al Asistente Virtual del Carnaval."""
    message: str = Field(..., min_length=1, description="Pregunta o mensaje del usuario.")
    user_latitude: Optional[float] = Field(None, description="Latitud actual del usuario para contexto geográfico.")
    user_longitude: Optional[float] = Field(None, description="Longitud actual del usuario para contexto geográfico.")
    user_lat: Optional[float] = Field(None, description="Alias para latitud actual del usuario.")
    user_lng: Optional[float] = Field(None, description="Alias para longitud actual del usuario.")
    selected_day: Optional[str] = Field(None, description="Día actualmente seleccionado en el cronograma del Carnaval (ej: '04-ene', '06-ene').")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "¿Qué va a haber hoy 4 de enero y qué restaurantes de cuy están abiertos?",
                "user_lat": 1.2136,
                "user_lng": -77.2811,
                "selected_day": "04-ene"
            }
        }
    }


class MapAction(BaseModel):
    """Acción interactiva para ejecutar en el mapa."""
    type: str = Field("ROUTE", description="Tipo de acción, ej: 'ROUTE'")
    target_name: str = Field(..., description="Nombre del sitio destino")
    target_coords: List[float] = Field(..., description="Coordenadas destino [lat, lng]")
    route_coords: List[List[float]] = Field(..., description="Puntos de la ruta [[lat1, lng1], [lat2, lng2], ...]")


class ChatResponse(BaseModel):
    """Esquema de respuesta generada por el Asistente Virtual."""
    response: str = Field(..., description="Respuesta conversacional generada por el asistente virtual con IA.")
    reply: Optional[str] = Field(None, description="Alias de texto conversacional para frontend.")
    action: Optional[Dict[str, Any]] = Field(None, description="Acción de navegación para el mapa interactivo.")
    sources_used: Optional[List[str]] = Field(default=None, description="Fuentes de información o entidades consultadas en tiempo real.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "response": "¡Hola, paisano! Con gusto te guío hacia el Restaurante Cuyquer...",
                "reply": "¡Hola, paisano! Con gusto te guío hacia el Restaurante Cuyquer...",
                "action": {
                    "type": "ROUTE",
                    "target_name": "Restaurante Cuyquer",
                    "target_coords": [1.2160, -77.2915],
                    "route_coords": [[1.2136, -77.2811], [1.2148, -77.2860], [1.2160, -77.2915]]
                },
                "sources_used": [
                    "Directorio Gastronómico: Restaurantes de Pasto",
                    "Geolocalización GPS activa"
                ]
            }
        }
    }
