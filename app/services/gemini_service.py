"""Gemini 2.5 Flash service for GuaneñaBot conversational AI and GIS route extraction.

Integrates Google Gemini 2.5 Flash to provide authentic Pastuso cultural guidance
for the Carnaval de Negros y Blancos, extracting geospatial coordinates for Leaflet/OSRM maps.
"""
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.core.config import settings

logger = logging.getLogger(__name__)

# ==============================================================================
# PASTO & SENDA DEL CARNAVAL GIS LANDMARKS DATABASE
# ==============================================================================
PASTO_LANDMARKS: Dict[str, List[float]] = {
    "Plaza del Carnaval": [1.2136, -77.2785],
    "Plaza de Nariño": [1.2148, -77.2780],
    "Estadio Libertad (Inicio Senda)": [1.2025, -77.2762],
    "Glorieta Lorenzo de Aldana": [1.2095, -77.2770],
    "Avenida de los Estudiantes / Fuente de la Transparencia (Fin Senda)": [1.2330, -77.2845],
    "Templo San Juan Bautista": [1.2155, -77.2798],
}

# The complete official Senda del Carnaval parade route sequence (South to North)
SENDA_OFFICIAL_ROUTE: List[List[float]] = [
    [1.2025, -77.2762],  # Estadio Libertad (Inicio Senda)
    [1.2095, -77.2770],  # Glorieta Lorenzo de Aldana
    [1.2136, -77.2785],  # Plaza del Carnaval y la Cultura
    [1.2148, -77.2780],  # Carrera 27 / Cruce Plaza de Nariño
    [1.2220, -77.2815],  # Carrera 27 hacia el norte
    [1.2330, -77.2845],  # Avenida de los Estudiantes / Fuente de la Transparencia (Fin Senda)
]

# Aliases dictionary for quick fuzzy matching
LANDMARK_ALIASES: Dict[str, Dict[str, Any]] = {
    "plaza del carnaval": {
        "name": "Plaza del Carnaval",
        "coords": [1.2136, -77.2785],
        "keywords": ["plaza del carnaval", "plaza carnaval", "concha acustica"],
    },
    "plaza de nariño": {
        "name": "Plaza de Nariño",
        "coords": [1.2148, -77.2780],
        "keywords": ["plaza de nariño", "plaza nariño", "plaza de narino", "plaza narino", "parque nariño"],
    },
    "estadio libertad": {
        "name": "Estadio Libertad (Inicio Senda)",
        "coords": [1.2025, -77.2762],
        "keywords": ["estadio libertad", "estadio", "inicio de la senda", "salida senda", "partida"],
    },
    "glorieta lorenzo": {
        "name": "Glorieta Lorenzo de Aldana",
        "coords": [1.2095, -77.2770],
        "keywords": ["glorieta lorenzo", "lorenzo de aldana", "lorenzo"],
    },
    "avenida estudiantes": {
        "name": "Avenida de los Estudiantes / Fuente de la Transparencia (Fin Senda)",
        "coords": [1.2330, -77.2845],
        "keywords": ["avenida de los estudiantes", "av estudiantes", "fuente de la transparencia", "fin de la senda", "llegada"],
    },
    "templo san juan": {
        "name": "Templo San Juan Bautista",
        "coords": [1.2155, -77.2798],
        "keywords": ["templo san juan bautista", "san juan bautista", "iglesia san juan", "templo san juan"],
    },
}

# ==============================================================================
# SYSTEM PROMPT FOR GUANEÑABOT (AUTHENTIC PASTUSO PERSONA)
# ==============================================================================
GUANENA_SYSTEM_PROMPT = """You are GuaneñaBot, the official AI guide of Carnaval de Negros y Blancos in San Juan de Pasto, declared UNESCO Intangible Cultural Heritage. You guide tourists and locals across dates (Jan 2: Ofrenda a la Virgen de las Mercedes, Jan 3: Canto a la Tierra, Jan 4: Familia Castañeda, Jan 5: Día de Negros, Jan 6: Día de Blancos). When users ask for directions, places, or tours, explain warmly and identify the exact geographic route points.

Personality & Tone:
- Speak in authentic, hospitable, enthusiastic Pastuso/Colombian Spanish.
- Use regional expressions warmly and respectfully: "¡Qué viva Pasto, carajo!", "veci", "guagua", "a la orden", "paisano".
- Provide rich historical context and carnival culture.

Geographic Landmarks in Pasto:
- Plaza del Carnaval: [1.2136, -77.2785]
- Plaza de Nariño: [1.2148, -77.2780]
- Estadio Libertad (Inicio Senda): [1.2025, -77.2762]
- Glorieta Lorenzo de Aldana: [1.2095, -77.2770]
- Avenida de los Estudiantes / Fuente de la Transparencia (Fin Senda): [1.2330, -77.2845]
- Templo San Juan Bautista: [1.2155, -77.2798]

Route Extraction Guidelines:
1. If the user asks for directions, how to get somewhere, a path, tour, or the Senda route:
   - Set "should_draw_route" to true.
   - In "waypoints", provide the array of coordinates [[lat, lng], [lat, lng], ...] representing the route sequence or destination.
   - For the full Senda del Carnaval parade route, return the full sequence:
     [[1.2025, -77.2762], [1.2095, -77.2770], [1.2136, -77.2785], [1.2148, -77.2780], [1.2220, -77.2815], [1.2330, -77.2845]]
2. If the user asks a general question about history, dates, or costumes without requesting navigation or a route:
   - Set "should_draw_route" to false.
   - "waypoints" can be empty or contain the single landmark mentioned.
3. Always supply 3 relevant, engaging "suggested_questions" for the user to continue exploring.
"""


# ==============================================================================
# PYDANTIC SCHEMA FOR STRUCTURED OUTPUT
# ==============================================================================
class GuaneñaStructuredResponse(BaseModel):
    """Structured response model generated by Gemini 2.5 Flash."""
    reply: str = Field(..., description="Warm Pastuso conversational response explaining the cultural context.")
    should_draw_route: bool = Field(..., description="True if a route or direction should be rendered on map.")
    waypoints: List[List[float]] = Field(default=[], description="List of [latitude, longitude] pairs for Leaflet/OSRM.")
    suggested_questions: List[str] = Field(default=[], description="Three concise suggested follow-up questions.")


def _clean_json_text(raw_text: str) -> str:
    """Strip markdown code fence blocks if present."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# ==============================================================================
# DETERMINISTIC FALLBACK ENGINE
# ==============================================================================
def _deterministic_fallback(message: str) -> Dict[str, Any]:
    """Provide high-fidelity cultural responses and GIS coordinates if Gemini API is unreachable."""
    msg = message.lower().strip()

    # Case 1: Route of the Senda del Carnaval / Full Tour
    if any(k in msg for k in ["senda", "recorrido", "ruta del desfile", "trayecto", "desfile magno ruta", "camino"]):
        return {
            "reply": (
                "¡Qué viva Pasto, carajo, veci! La majestuosa Senda del Carnaval recorre aproximadamente 7 kilómetros "
                "de fervor y alegría popular. El desfile arranca en el sur en el Estadio Libertad, avanza por la Glorieta "
                "Lorenzo de Aldana, atraviesa la Plaza del Carnaval y la Carrera 27 junto a la Plaza de Nariño, y culmina "
                "al norte en la Avenida de los Estudiantes junto a la Fuente de la Transparencia. ¡Aquí le trazo la ruta completa en el mapa!"
            ),
            "should_draw_route": True,
            "waypoints": SENDA_OFFICIAL_ROUTE,
            "suggested_questions": [
                "¿Dónde queda la Plaza del Carnaval?",
                "¿A qué hora arranca el desfile del 6 de enero?",
                "¿Qué se celebra el 4 de enero con la Familia Castañeda?"
            ]
        }

    # Case 2: Plaza del Carnaval
    if any(k in msg for k in ["plaza del carnaval", "plaza carnaval", "concha acústica", "concha acustica"]):
        coords = PASTO_LANDMARKS["Plaza del Carnaval"]
        return {
            "reply": (
                "¡A la orden, veci! La Plaza del Carnaval y la Cultura es el corazón palpitante de nuestra fiesta. "
                "Allí se concentran las graderías oficiales, la gran tarima de orquestas y las premiaciones de las "
                "monumentales carrozas. Se ubica en las coordenadas [1.2136, -77.2785]. ¡Ya le marco el punto en el mapa!"
            ),
            "should_draw_route": True,
            "waypoints": [coords],
            "suggested_questions": [
                "¿Cómo llegar a la Plaza del Carnaval desde el Estadio Libertad?",
                "¿Qué eventos se realizan en la Plaza del Carnaval?",
                "¿Dónde queda la Plaza de Nariño?"
            ]
        }

    # Case 3: Plaza de Nariño / Templo San Juan
    if any(k in msg for k in ["plaza de nariño", "plaza nariño", "plaza narino", "templo san juan", "san juan bautista"]):
        coords = PASTO_LANDMARKS["Plaza de Nariño"]
        return {
            "reply": (
                "¡Bienvenido al centro histórico de San Juan de Pasto, paisano! La Plaza de Nariño y el contiguo Templo "
                "de San Juan Bautista son testigos del tradicional Día de Negros el 5 de enero, donde jugamos con la "
                "fraternal pintica de cosmético al son de murgas tradicionales. Coordenadas: [1.2148, -77.2780]."
            ),
            "should_draw_route": True,
            "waypoints": [coords],
            "suggested_questions": [
                "¿Qué actividades hay el 5 de enero en la Plaza de Nariño?",
                "¿Cómo ir de la Plaza de Nariño a la Plaza del Carnaval?",
                "¿Dónde puedo probar empanadas de añejo?"
            ]
        }

    # Case 4: Estadio Libertad (Inicio Senda)
    if any(k in msg for k in ["estadio libertad", "estadio", "salida", "inicio", "arranca"]):
        coords = PASTO_LANDMARKS["Estadio Libertad (Inicio Senda)"]
        return {
            "reply": (
                "¡Qué viva Pasto, carajo! El Estadio Libertad, al sur de la ciudad, es el tradicional punto de partida "
                "y concentración de los colectivos coreográficos, carrozas y murgas antes de entrar a la Senda. "
                "Coordenadas de salida: [1.2025, -77.2762]."
            ),
            "should_draw_route": True,
            "waypoints": [coords],
            "suggested_questions": [
                "¿Cuál es el recorrido completo desde el Estadio Libertad?",
                "¿Qué desfiles salen desde el Estadio Libertad?",
                "¿Dónde termina la Senda del Carnaval?"
            ]
        }

    # Case 5: Avenida de los Estudiantes / Fin Senda
    if any(k in msg for k in ["avenida de los estudiantes", "estudiantes", "fuente de la transparencia", "fin de la senda", "llegada"]):
        coords = PASTO_LANDMARKS["Avenida de los Estudiantes / Fuente de la Transparencia (Fin Senda)"]
        return {
            "reply": (
                "¡Qué emoción, veci! La Avenida de los Estudiantes y la emblemática Fuente de la Transparencia "
                "marcan la meta y punto de desconcentración de los grandes desfiles tras recorrer la Carrera 27. "
                "Coordenadas de llegada: [1.2330, -77.2845]."
            ),
            "should_draw_route": True,
            "waypoints": [coords],
            "suggested_questions": [
                "¿Qué restaurantes tradicionales quedan cerca a la Avenida de los Estudiantes?",
                "¿Cómo es la ruta completa de la Senda?",
                "¿Qué día desfilan las carrozas monumentales?"
            ]
        }

    # Case 6: Jan 4 - Familia Castañeda
    if any(k in msg for k in ["familia castañeda", "castañeda", "castaneda", "4 de enero", "cuatro de enero"]):
        return {
            "reply": (
                "¡Abran cancha que llegó la Familia Castañeda, veci! El 4 de enero revivimos la histórica llegada de "
                "esta comitiva campesina en 1929. El desfile recrea cuadros costumbristas, carretas de época y personajes "
                "típicos saludando a propios y visitantes. La caravana recorre la Senda desde el sur hasta el centro."
            ),
            "should_draw_route": True,
            "waypoints": [PASTO_LANDMARKS["Estadio Libertad (Inicio Senda)"], PASTO_LANDMARKS["Plaza del Carnaval"]],
            "suggested_questions": [
                "¿A qué hora empieza la Familia Castañeda?",
                "¿Dónde ver mejor el desfile del 4 de enero?",
                "¿Qué desfile sigue el 5 de enero?"
            ]
        }

    # Case 7: Jan 6 - Día de Blancos / Carrozas
    if any(k in msg for k in ["6 de enero", "seis de enero", "blancos", "carroza", "magno"]):
        return {
            "reply": (
                "¡La cumbre monumental de nuestra fiesta, paisano! El 6 de enero es el Día de Blancos y el Desfile Magno. "
                "Nuestros maestros artesanos exhiben gigantescas obras de arte rodante de hasta 12 metros de altura, "
                "acompañadas de miles de danzantes y el alegre juego con talco y carioca. Todo arranca en el Estadio Libertad."
            ),
            "should_draw_route": True,
            "waypoints": SENDA_OFFICIAL_ROUTE,
            "suggested_questions": [
                "¿Cuál es el recorrido del Desfile Magno?",
                "¿Qué medidas de seguridad debo tener para el talco y carioca?",
                "¿Dónde termina el desfile del 6 de enero?"
            ]
        }

    # Default friendly Pastuso response
    return {
        "reply": (
            "¡Qué viva Pasto, carajo, veci! Soy GuaneñaBot, su guía oficial del Carnaval de Negros y Blancos. "
            "Puedo orientarle sobre la programación (2 de enero al 7 de enero), trazarle la ruta de la Senda del Carnaval "
            "o indicarle las coordenadas exactas de la Plaza del Carnaval, la Plaza de Nariño y el Estadio Libertad. ¿Para dónde vamos hoy?"
        ),
        "should_draw_route": False,
        "waypoints": [],
        "suggested_questions": [
            "¿Cuál es el recorrido oficial de la Senda del Carnaval?",
            "¿Dónde queda la Plaza del Carnaval?",
            "¿Qué se celebra el 6 de enero en Pasto?"
        ]
    }


# ==============================================================================
# MAIN CONVERSATIONAL DISPATCHER FUNCTION
# ==============================================================================
def chat_with_guanena(message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """Execute conversational dispatching using Gemini 2.5 Flash with deterministic GIS fallback.

    Args:
        message: The natural language prompt from the user.
        chat_history: Optional list of previous message turns.

    Returns:
        Dict matching CarnavalChatResponse schema:
        - reply: str
        - should_draw_route: bool
        - waypoints: List[List[float]]
        - suggested_questions: List[str]
    """
    if chat_history is None:
        chat_history = []

    api_key = settings.GEMINI_API_KEY.strip() if hasattr(settings, "GEMINI_API_KEY") else ""
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")

    # If valid Gemini API key is configured and google-genai is available
    if api_key and api_key not in ["tu_clave_de_gemini_aqui", ""] and genai is not None:
        try:
            client = genai.Client(api_key=api_key)

            # Build history string
            history_context = ""
            if chat_history:
                formatted_history = "\n".join(
                    f"{turn.get('role', 'user')}: {turn.get('content', '')}"
                    for turn in chat_history[-6:]
                )
                history_context = f"\nPrevious Conversation:\n{formatted_history}\n"

            prompt_content = f"""{history_context}
User Query: "{message}"

Please respond according to your persona and structured JSON schema.
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=GUANENA_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=GuaneñaStructuredResponse,
                    temperature=0.3,
                )
            )

            if response and response.text:
                cleaned_text = _clean_json_text(response.text)
                data = json.loads(cleaned_text)
                return {
                    "reply": data.get("reply", "¡Qué viva Pasto, carajo!"),
                    "should_draw_route": bool(data.get("should_draw_route", False)),
                    "waypoints": data.get("waypoints", []),
                    "suggested_questions": data.get("suggested_questions", [
                        "¿Cuál es el recorrido de la Senda?",
                        "¿Dónde queda la Plaza del Carnaval?",
                        "¿Qué se celebra el 6 de enero?"
                    ])
                }
        except Exception as exc:
            logger.warning(
                f"[GEMINI_SERVICE] Notice while querying Gemini 2.5 Flash ({type(exc).__name__}: {exc}). "
                "Engaging deterministic cultural GIS fallback."
            )

    # Deterministic fallback when Gemini API is unavailable or offline
    return _deterministic_fallback(message)
