"""Servicio del Asistente Turístico y Cultural GuaneñaBot con Google Gemini.

Procesa lenguaje natural de turistas y ciudadanos para responder con contexto cultural
y devolver acciones deterministas de mapa para el Carnaval de Negros y Blancos de Pasto.
"""
import json
import logging
from typing import Any, Dict, Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.carnaval_knowledge import CARNAVAL_EVENTS, EXTRA_POIS_KNOWLEDGE
from app.schemas.chat_schema import ChatRequest, ChatResponse, MapAction

logger = logging.getLogger(__name__)

# ==============================================================================
# PROMPT DE SISTEMA OFICIAL DE GUANEÑABOT
# ==============================================================================
GUANENA_SYSTEM_PROMPT = """Eres GuaneñaBot, el asistente turístico y cultural oficial del Carnaval de Negros y Blancos en Pasto, Nariño. Eres cordial, conocedor y usas expresiones pastusas respetuosas ('¡Qué viva Pasto, carajo!', 'veci', 'guagua').
Cuando un usuario pregunte por un evento o dónde empieza un desfile (ej. 4 de enero / Familia Castañeda), debes:
1. Explicar brevemente la tradición del día (2 a 3 líneas).
2. Identificar el punto de partida exacto (generalmente Senda Champagnat al sur de la ciudad).
3. Devolver OBLIGATORIAMENTE un JSON con 'reply' y 'map_action' con action_type: 'ROUTE_TO_EVENT_START', target_name y sus target_coords.

Puntos de partida oficiales:
- 28 Dic (Arcoíris en el Asfalto): [1.2140, -77.2785] (Calle 18 / Plaza del Carnaval)
- 31 Dic (Años Viejos): [1.2052, -77.2796] (Senda Champagnat / Parque Bolívar)
- 02 Ene (Carnavalito): [1.2138, -77.2782] (Plaza del Carnaval)
- 03 Ene (Canto a la Tierra): [1.2052, -77.2796] (Senda Champagnat / Sur)
- 04 Ene (Familia Castañeda): [1.2052, -77.2796] (Senda Champagnat / Sur)
- 05 Ene (Día de Negros): [1.2168, -77.2805] (Plaza de Nariño)
- 06 Ene (Desfile Magno): [1.2052, -77.2796] (Senda Champagnat / Sur)
- 07 Ene (Festival del Cuy): [1.2020, -77.2910] (Catambuco / Obonuco)

Si el usuario consulta por comida típica (cuy, empanadas de añejo), salud/primeros auxilios o baños, responde cordialmente y emite el map_action correspondiente (ej. action_type: 'FILTER_POIS' o 'ROUTE_TO_EVENT_START' con sus coordenadas).
Si es una charla sin necesidad de mapa, map_action puede ser null o action_type 'INFO_ONLY'.
Debes responder ÚNICAMENTE un objeto JSON válido con las claves 'reply' y 'map_action'.
"""


def _parse_gemini_json_response(raw_text: str) -> Dict[str, Any]:
    """Limpia etiquetas de markdown y convierte la salida de Gemini a diccionario."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())


def process_guanena_chat(request: ChatRequest) -> ChatResponse:
    """Envía la consulta del usuario al modelo Gemini con System Prompt y formato JSON estricto."""
    # Contexto geográfico del usuario si se suministra
    loc_context = ""
    if request.user_lat is not None and request.user_lng is not None:
        loc_context = f"\nUbicación actual del usuario: Latitud {request.user_lat}, Longitud {request.user_lng}."

    user_prompt = f"""CONSULTA DEL TURISTA/CIUDADANO:
"{request.message}"
{loc_context}
"""

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=GUANENA_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ChatResponse,
            temperature=0.3,
        )
    )

    if response and response.text:
        parsed = _parse_gemini_json_response(response.text)
        action_data = parsed.get("map_action")
        map_action = MapAction(**action_data) if action_data else None
        return ChatResponse(
            reply=parsed.get("reply", "¡Qué viva Pasto, carajo!"),
            map_action=map_action
        )

    return ChatResponse(
        reply="¡Qué viva Pasto, carajo! ¿En qué más le puedo colaborar, veci?",
        map_action=None
    )
