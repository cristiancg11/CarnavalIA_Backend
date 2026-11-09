"""Gemini 2.5 Flash service for GuaneñaBot conversational AI and full GIS telemetry.

Integrates Google Gemini 2.5 Flash to provide authentic Pastuso cultural guidance
for the Carnaval de Negros y Blancos, extracting geospatial coordinates for Leaflet/OSRM maps,
official parade schedules, route polylines, and nearby service layers (restrooms, police,
first aid, stages, shopping, and congestion risk zones).
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.core.config import settings
from app.services.carnaval_gis_data import (
    SENDA_START,
    SENDA_FINISH,
    SENDA_OFFICIAL_PATH,
    NEARBY_SERVICE_POINTS,
    CARNAVAL_SCHEDULES,
    get_schedule_for_query,
)

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
SENDA_OFFICIAL_ROUTE: List[List[float]] = SENDA_OFFICIAL_PATH


# ==============================================================================
# SYSTEM PROMPT FOR GUANEÑABOT (AUTHENTIC PASTUSO PERSONA & TELEMETRY)
# ==============================================================================
GUANENA_SYSTEM_PROMPT = """You are GuaneñaBot, the official AI guide of Carnaval de Negros y Blancos in San Juan de Pasto, declared UNESCO Intangible Cultural Heritage. You guide tourists and locals across dates:
- Jan 2: Ofrenda a la Virgen de las Mercedes y Carnavalito (Starts ~9:00 AM at Templo San Juan, finishes ~1:30 PM at Santuario Las Mercedes).
- Jan 3: Canto a la Tierra - Desfile de Colectivos Coreográficos (Starts ~10:00 AM at Estadio Libertad, finishes ~3:00 PM at Plaza del Carnaval).
- Jan 4: Llegada de la Familia Castañeda (Starts ~10:00 AM at Estadio Libertad, finishes ~3:30 PM at Avenida de los Estudiantes).
- Jan 5: Día de Negros - Juego de Cosmético (All day celebration 8:00 AM to 8:00 PM, centered at Plaza de Nariño and public plazas).
- Jan 6: Desfile Magno - Día de Blancos / Carrozas Monumentales (Starts 9:00 AM at Estadio Libertad, finishes ~4:30 PM at Avenida de los Estudiantes / Torobajo).
- Jan 7: Festival del Cuy y la Cultura Campesina (Starts ~10:00 AM in Catambuco and Obonuco).

When users ask for directions, places, or tours, explain warmly and identify the exact geographic route points, schedule, and nearby services.

Personality & Tone:
- Speak in authentic, hospitable, enthusiastic Pastuso/Colombian Spanish.
- Use regional expressions warmly and respectfully: "¡Qué viva Pasto, carajo!", "veci", "guagua", "a la orden", "paisano".
- Provide rich historical context and safety recommendations.

Official Senda Path (South to North through Pasto):
[[1.2025, -77.2762], [1.2052, -77.2766], [1.2095, -77.2770], [1.2115, -77.2778], [1.2136, -77.2785], [1.2142, -77.2782], [1.2148, -77.2780], [1.2190, -77.2800], [1.2260, -77.2825], [1.2330, -77.2845]]

Nearby Service Categories:
- restroom: Public baths and portable toilet points (e.g. Plaza del Carnaval [1.2130, -77.2780], Pasaje Corazón de Jesús [1.2152, -77.2775], Estadio Libertad [1.2030, -77.2758])
- police: CAI security posts (e.g. CAI Plaza Nariño [1.2140, -77.2792], CAI Lorenzo [1.2088, -77.2765], CAI Morasurco [1.2290, -77.2830])
- health: Emergency first aid / Red Cross tents (e.g. Cruz Roja Plaza Carnaval [1.2128, -77.2779], Puesto Calle 19 Cra 27 [1.2195, -77.2801])
- stage: Concert and orchestra stages (e.g. Plaza del Carnaval [1.2136, -77.2785], Plaza de Nariño [1.2148, -77.2780], Plaza del Carrizal [1.2225, -77.2815])
- shopping: Commercial centers (e.g. CC Sebastián de Belalcázar [1.2160, -77.2765], CC Unicentro Pasto [1.2285, -77.2835])
- risk_zone: High congestion crowd bottleneck zones (e.g. Embudo Cra 27 Plaza Carnaval [1.2135, -77.2788])

Instructions for Structured Output:
1. "reply": Detailed advice, historical context, and safety recommendations in authentic Pastuso Spanish.
2. "schedule": Estimated schedule with "start_time", "estimated_arrival_time", "start_location", "finish_location" based on the carnival day discussed.
3. "should_draw_route": Set true if user asks for directions, a path, the Senda route, or a tour.
4. "route_coordinates": List of [lat, lng] points for the street path.
5. "nearby_places": Relevant nearby services selected from restroom, police, health, stage, shopping, and risk_zone with name, category, coordinates, and description.
6. "suggested_questions": 3 follow-up prompt questions.
"""


# ==============================================================================
# PYDANTIC SCHEMAS FOR STRUCTURED GEMINI INFERENCE
# ==============================================================================
class CarnavalScheduleSchema(BaseModel):
    """Event schedule structure generated by Gemini 2.5 Flash."""
    start_time: str = Field(..., description="Scheduled start time (e.g. '10:00 AM')")
    estimated_arrival_time: str = Field(..., description="Estimated finish time (e.g. '3:30 PM')")
    start_location: str = Field(..., description="Starting location name (e.g. 'Estadio Libertad')")
    finish_location: str = Field(..., description="Finishing location name (e.g. 'Avenida de los Estudiantes')")


class NearbyPlaceSchema(BaseModel):
    """Nearby service point or risk zone along the route."""
    name: str = Field(..., description="Name of the service or landmark")
    category: str = Field(..., description="Category: restroom, police, health, stage, restaurant, shopping, risk_zone")
    coordinates: List[float] = Field(..., description="[latitude, longitude] in Pasto")
    description: str = Field(..., description="Brief description or safety note")


class GuaneñaStructuredResponse(BaseModel):
    """Full structured response model generated by Gemini 2.5 Flash."""
    reply: str = Field(..., description="Warm Pastuso conversational response explaining cultural and GIS details.")
    schedule: Optional[CarnavalScheduleSchema] = Field(
        default=None,
        description="Parade departure and arrival schedule estimates."
    )
    should_draw_route: bool = Field(..., description="True if a route or direction should be rendered on map.")
    route_coordinates: List[List[float]] = Field(
        default=[],
        description="List of [latitude, longitude] pairs for Leaflet Polyline."
    )
    nearby_places: List[NearbyPlaceSchema] = Field(
        default=[],
        description="Strategic public services and risk zones near the route."
    )
    suggested_questions: List[str] = Field(
        default=[],
        description="Three concise suggested follow-up questions."
    )


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
# DETERMINISTIC FALLBACK ENGINE WITH FULL TELEMETRY
# ==============================================================================
def _deterministic_fallback(message: str) -> Dict[str, Any]:
    """Provide high-fidelity cultural responses, schedule, route, and nearby layers."""
    msg = message.lower().strip()
    schedule_data = get_schedule_for_query(message)

    # Filter nearby places or provide all official points
    nearby_points = NEARBY_SERVICE_POINTS

    # Case 1: Route of the Senda del Carnaval / Full Tour
    if any(k in msg for k in ["senda", "recorrido", "ruta del desfile", "trayecto", "desfile magno ruta", "camino"]):
        return {
            "reply": (
                "¡Qué viva Pasto, carajo, veci! La majestuosa Senda del Carnaval recorre aproximadamente 7 kilómetros "
                "de fervor y alegría popular. El desfile arranca en el sur en el Estadio Libertad, avanza por la Glorieta "
                "Lorenzo de Aldana, atraviesa la Plaza del Carnaval y la Carrera 27 junto a la Plaza de Nariño, y culmina "
                "al norte en la Avenida de los Estudiantes junto a la Fuente de la Transparencia. "
                "¡Le he trazado la ruta oficial completa, el horario programado y todos los puntos de auxilio, baños y tarimas!"
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": SENDA_OFFICIAL_PATH,
            "waypoints": SENDA_OFFICIAL_PATH,
            "nearby_places": nearby_points,
            "suggested_questions": [
                "¿Dónde quedan los baños y puestos de salud en la Plaza del Carnaval?",
                "¿A qué hora arranca el desfile del 6 de enero?",
                "¿Qué se celebra el 4 de enero con la Familia Castañeda?"
            ]
        }

    # Case 2: Baños / Servicios Sanitarios
    if any(k in msg for k in ["baño", "baños", "sanitario", "servicios sanitarios", "restroom"]):
        restrooms = [p for p in nearby_points if p["category"] == "restroom"]
        return {
            "reply": (
                "¡A la orden, veci! Durante los días de Carnaval tenemos baterías de baños públicos y módulos portátiles "
                "estratégicamente ubicados en la Plaza del Carnaval, el Pasaje Corazón de Jesús (centro) y en las inmediaciones "
                "del Estadio Libertad. ¡Aquí le marco las ubicaciones en el mapa para que no pase apuros!"
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": [[p["coordinates"][0], p["coordinates"][1]] for p in restrooms],
            "waypoints": [[p["coordinates"][0], p["coordinates"][1]] for p in restrooms],
            "nearby_places": restrooms,
            "suggested_questions": [
                "¿Dónde queda el puesto de salud más cercano?",
                "¿Cuál es el recorrido de la Senda del Carnaval?",
                "¿Dónde queda la Plaza del Carnaval?"
            ]
        }

    # Case 3: Seguridad / Policía / CAI
    if any(k in msg for k in ["policia", "policía", "cai", "seguridad", "denuncia", "robo"]):
        police_points = [p for p in nearby_points if p["category"] == "police"]
        return {
            "reply": (
                "¡Tranquilo, paisano! La Policía Metropolitana tiene instalados CAI de atención inmediata y cuadrantes en "
                "la Plaza de Nariño, la Glorieta Lorenzo de Aldana y en Morasurco sobre la Avenida de los Estudiantes. "
                "Recomendación carnavalera: cuide sus objetos personales, evite el uso excesivo del celular en aglomeraciones "
                "y acuda de inmediato a cualquiera de estos puntos."
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": [[p["coordinates"][0], p["coordinates"][1]] for p in police_points],
            "waypoints": [[p["coordinates"][0], p["coordinates"][1]] for p in police_points],
            "nearby_places": police_points,
            "suggested_questions": [
                "¿Dónde queda el CAI de la Plaza de Nariño?",
                "¿Cuáles son las zonas de mayor aglomeración?",
                "¿Dónde están los puestos de la Cruz Roja?"
            ]
        }

    # Case 4: Salud / Cruz Roja / Primeros Auxilios
    if any(k in msg for k in ["salud", "cruz roja", "primeros auxilios", "ambulancia", "medico", "médico", "emergencia"]):
        health_points = [p for p in nearby_points if p["category"] == "health"]
        return {
            "reply": (
                "¡Para servirle, veci! Si presenta alguna emergencia médica, la Cruz Roja y la Defensa Civil cuentan con puestos "
                "de triage y ambulancias permanentes junto a la Plaza del Carnaval y en el cruce de la Calle 19 con Carrera 27. "
                "¡Cuídese los ojitos del talco y manténgase bien hidratado!"
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": [[p["coordinates"][0], p["coordinates"][1]] for p in health_points],
            "waypoints": [[p["coordinates"][0], p["coordinates"][1]] for p in health_points],
            "nearby_places": health_points,
            "suggested_questions": [
                "¿Dónde queda el puesto de salud de la Plaza del Carnaval?",
                "¿Dónde puedo comprar gafas protectoras para el talco?",
                "¿Cómo llegar a la Plaza de Nariño?"
            ]
        }

    # Case 5: Tarimas / Música / Conciertos
    if any(k in msg for k in ["tarima", "concierto", "musica", "música", "orquesta", "escenario"]):
        stage_points = [p for p in nearby_points if p["category"] == "stage"]
        return {
            "reply": (
                "¡A gozar y a bailar, veci! Las tres tarimas oficiales del Carnaval están encendidas: la Tarima Principal en la "
                "Plaza del Carnaval con grandes orquestas, la Tarima Cultural en la Plaza de Nariño con música andina y danza tradicional, "
                "y la Tarima Alternativa en el Carrizal con son sureño y música campesina."
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": [[p["coordinates"][0], p["coordinates"][1]] for p in stage_points],
            "waypoints": [[p["coordinates"][0], p["coordinates"][1]] for p in stage_points],
            "nearby_places": stage_points,
            "suggested_questions": [
                "¿Quién se presenta en la Plaza del Carnaval?",
                "¿A qué hora terminan los conciertos en las plazas?",
                "¿Dónde queda la Plaza del Carrizal?"
            ]
        }

    # Case 6: Jan 4 - Familia Castañeda
    if any(k in msg for k in ["familia castañeda", "castañeda", "castaneda", "4 de enero"]):
        jan4_sched = CARNAVAL_SCHEDULES["jan_04"]
        return {
            "reply": (
                "¡Abran cancha que llegó la Familia Castañeda, veci! El 4 de enero conmemoramos la histórica llegada de "
                "esta alegre familia en 1929. El desfile arranca a las 10:00 AM en el Estadio Libertad y arriba hacia las "
                "3:30 PM a la Avenida de los Estudiantes con estampas de arrieros, carretas campesinas y el saludo de Don Pericles Carnaval."
            ),
            "schedule": jan4_sched,
            "should_draw_route": True,
            "route_coordinates": SENDA_OFFICIAL_PATH,
            "waypoints": SENDA_OFFICIAL_PATH,
            "nearby_places": nearby_points,
            "suggested_questions": [
                "¿A qué hora empieza la Familia Castañeda?",
                "¿Dónde ver mejor el desfile del 4 de enero?",
                "¿Qué desfile sigue el 5 de enero?"
            ]
        }

    # Case 7: Jan 6 - Desfile Magno / Carrozas
    if any(k in msg for k in ["6 de enero", "blancos", "carroza", "magno"]):
        jan6_sched = CARNAVAL_SCHEDULES["jan_06"]
        return {
            "reply": (
                "¡La cumbre monumental de nuestra fiesta, paisano! El 6 de enero es el Día de Blancos y el Desfile Magno. "
                "Nuestros maestros artesanos exhiben gigantescas carrozas de hasta 12 metros de altura acompañadas de murgas y comparsas. "
                "El desfile inicia a las 9:00 AM en el Estadio Libertad y culmina aproximadamente a las 4:30 PM en la Avenida de los Estudiantes."
            ),
            "schedule": jan6_sched,
            "should_draw_route": True,
            "route_coordinates": SENDA_OFFICIAL_PATH,
            "waypoints": SENDA_OFFICIAL_PATH,
            "nearby_places": nearby_points,
            "suggested_questions": [
                "¿Cuál es el recorrido del Desfile Magno?",
                "¿Dónde están ubicados los baños en la ruta?",
                "¿Dónde termina el desfile del 6 de enero?"
            ]
        }

    # Default friendly Pastuso response with telemetry
    return {
        "reply": (
            "¡Qué viva Pasto, carajo, veci! Soy GuaneñaBot, su guía oficial del Carnaval de Negros y Blancos. "
            "Puedo informarle sobre los horarios de salida y llegada de los desfiles, trazarle la Senda del Carnaval "
            "en el mapa, y mostrarle los puntos de baños (🚻), puestos de salud (🚑), CAI policiales (👮), tarimas musicales (🎪) "
            "y zonas de alta aglomeración (⚠️). ¿En qué le puedo colaborar hoy?"
        ),
        "schedule": schedule_data,
        "should_draw_route": True,
        "route_coordinates": SENDA_OFFICIAL_PATH,
        "waypoints": SENDA_OFFICIAL_PATH,
        "nearby_places": nearby_points,
        "suggested_questions": [
            "¿Cuál es el recorrido oficial de la Senda del Carnaval?",
            "¿Dónde quedan los baños y puestos de salud?",
            "¿A qué hora empieza el Desfile Magno del 6 de enero?"
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
        Dict matching CarnavalChatResponse schema with schedule, route, and nearby places.
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

Please respond according to your persona and structured JSON schema including schedule, route_coordinates, and nearby_places.
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

                route_coords = data.get("route_coordinates", [])
                if not route_coords and data.get("should_draw_route"):
                    route_coords = SENDA_OFFICIAL_PATH

                schedule_obj = data.get("schedule")
                if not schedule_obj:
                    schedule_obj = get_schedule_for_query(message)

                nearby_places = data.get("nearby_places", [])
                if not nearby_places:
                    nearby_places = NEARBY_SERVICE_POINTS

                return {
                    "reply": data.get("reply", "¡Qué viva Pasto, carajo!"),
                    "schedule": schedule_obj,
                    "should_draw_route": bool(data.get("should_draw_route", False)),
                    "route_coordinates": route_coords,
                    "waypoints": route_coords,
                    "nearby_places": nearby_places,
                    "suggested_questions": data.get("suggested_questions", [
                        "¿Dónde quedan los baños públicos?",
                        "¿Cuál es el recorrido de la Senda?",
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
