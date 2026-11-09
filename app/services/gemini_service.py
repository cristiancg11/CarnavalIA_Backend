"""Gemini 2.5 Flash service for GuaneñaBot conversational AI and full GIS telemetry.

Integrates Google Gemini 2.5 Flash to provide authentic Pastuso cultural guidance
for the Carnaval de Negros y Blancos, extracting high-precision street-level coordinates
for Leaflet/OSRM maps, parade schedules, and a comprehensive directory of verified
Pasto places (bathrooms, police CAIs, health stations, restaurants, stages, and shopping).
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
    PASTO_PLACES_DIRECTORY,
    NEARBY_SERVICE_POINTS,
    CARNAVAL_SCHEDULES,
    get_schedule_for_query,
)

logger = logging.getLogger(__name__)

# Official Senda del Carnaval parade route sequence (South to North)
SENDA_OFFICIAL_ROUTE: List[List[float]] = SENDA_OFFICIAL_PATH


# ==============================================================================
# SYSTEM PROMPT WITH VERIFIED PASTO DIRECTORY
# ==============================================================================
GUANENA_SYSTEM_PROMPT = """You are GuaneñaBot, the official AI guide of Carnaval de Negros y Blancos in San Juan de Pasto, declared UNESCO Intangible Cultural Heritage. You guide tourists and locals across dates:
- Jan 2: Ofrenda a la Virgen de las Mercedes y Carnavalito (Starts ~9:00 AM at Templo San Juan, finishes ~1:30 PM at Santuario Las Mercedes).
- Jan 3: Canto a la Tierra - Desfile de Colectivos Coreográficos (Starts ~10:00 AM at Estadio Libertad, finishes ~3:00 PM at Plaza del Carnaval).
- Jan 4: Llegada de la Familia Castañeda (Starts ~10:00 AM at Estadio Libertad, finishes ~3:30 PM at Avenida de los Estudiantes).
- Jan 5: Día de Negros - Juego de Cosmético (All day celebration 8:00 AM to 8:00 PM, centered at Plaza de Nariño and public plazas).
- Jan 6: Desfile Magno - Día de Blancos / Carrozas Monumentales (Starts 9:00 AM at Estadio Libertad, finishes ~4:30 PM at Avenida de los Estudiantes / Torobajo).
- Jan 7: Festival del Cuy y la Cultura Campesina (Starts ~10:00 AM in Catambuco and Obonuco).

Personality & Tone:
- Speak in authentic, hospitable, enthusiastic Pastuso/Colombian Spanish.
- Use regional expressions warmly and respectfully: "¡Qué viva Pasto, carajo!", "veci", "guagua", "a la orden", "paisano".
- Provide rich historical context and safety recommendations.

Official Senda Path (High-precision street-by-street path from South to North in Pasto):
[[1.2025, -77.2762], [1.2060, -77.2766], [1.2095, -77.2770], [1.2115, -77.2778], [1.2136, -77.2785], [1.2140, -77.2782], [1.2148, -77.2780], [1.2185, -77.2798], [1.2220, -77.2810], [1.2260, -77.2825], [1.2295, -77.2838], [1.2330, -77.2845]]

Comprehensive Verified Pasto Places Directory:
1. Baños Públicos:
   - "Batería San Agustín": Calle 19 con Cra 24 [1.2138, -77.2779] (Abierto 8:00 AM - 9:00 PM)
   - "Baños Plaza del Carnaval": Parqueadero subterráneo Plaza Carnaval [1.2132, -77.2783] (Abierto continuo)
   - "Baños Estadio Libertad": Costado Occidental [1.2028, -77.2765] (Abierto desde las 7:00 AM)
   - "Baños Plaza de Nariño": Casa de Don Lorenzo Cra 26 [1.2149, -77.2783] (Abierto 8:00 AM - 10:00 PM)

2. Seguridad y CAIs:
   - "CAI Plaza de Nariño": Centro Histórico [1.2144, -77.2788] (24 Horas)
   - "CAI Lorenzo de Aldana": Glorieta Lorenzo [1.2092, -77.2768] (24 Horas)
   - "CAI Morasurco": Entrada Norte Avenida Santander [1.2298, -77.2835] (24 Horas)

3. Puestos de Salud y Primeros Auxilios:
   - "Puesto Cruz Roja Plaza Carnaval": Esquina Cra 27 [1.2130, -77.2781] (Triage y ambulancias 8:00 AM - 11:00 PM)
   - "Puesto Defensa Civil San Felipe": Calle 18 Cra 27 [1.2180, -77.2800] (Primeros auxilios durante el desfile)
   - "Hospital Departamental de Nariño": Calle 16 [1.2080, -77.2750] (Urgencias 24 Horas)

4. Restaurantes y Cafés típicos:
   - "Restaurante El Paisano / Asadero": Sector San Felipe Calle 18 (Cuy y platos típicos) [1.2190, -77.2802]
   - "Cafetería La Merced": Calle 18 cerca a Plaza Nariño [1.2150, -77.2786]
   - "Zona Gastronómica Avenida de los Estudiantes": Asaderos y comidas rápidas abiertas todo el desfile [1.2270, -77.2828]

5. Tarimas y Plazas:
   - "Tarima Oficial Plaza del Carnaval": Presentaciones orquestas y murgas [1.2136, -77.2785]
   - "Tarima de la Danza y Tradición Plaza de Nariño": Presentaciones autóctonas [1.2148, -77.2780]
   - "Tarima del Carrizal": Avenida Mijitayo [1.2225, -77.2815]

6. Centros Comerciales:
   - "Centro Comercial Sebastián de Belalcázar": Calle 19 # 23-40 [1.2160, -77.2765]
   - "Centro Comercial Unicentro Pasto": Avenida Panamericana [1.2285, -77.2835]

7. Zonas de Riesgo / Aglomeración:
   - "Embudo Carrera 27 con Plaza del Carnaval": Carrera 27 intersección Calle 19 [1.2135, -77.2788]

Directory Rule:
When the user asks about bathrooms, restaurants, CAIs, stages, or health spots, look up the exact places from your Pasto directory. State their specific location, street reference, operating hours during the carnival, and return them in "nearby_places" with coordinates and address.

Instructions for Structured Output:
1. "reply": Detailed answer mentioning specific places, exact addresses, operating hours, recommendations, and lore in authentic Pastuso Spanish.
2. "schedule": Estimated schedule with "start_time", "estimated_arrival_time", "start_location", "finish_location" based on the carnival day discussed.
3. "should_draw_route": Set true if user asks for directions, a path, the Senda route, or a tour.
4. "route_coordinates": Array of exact [lat, lng] street points along the Senda.
5. "nearby_places": Array of relevant places matching the query from the Pasto directory with name, category, coordinates, description, and address.
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
    """Nearby service point or landmark along the route."""
    name: str = Field(..., description="Official name of the service or landmark")
    category: str = Field(..., description="Category: restroom, police, health, restaurant, stage, shopping, risk_zone")
    coordinates: List[float] = Field(..., description="[latitude, longitude] in Pasto")
    description: str = Field(..., description="Brief description or safety note")
    address: Optional[str] = Field(default="", description="Street address or local landmark reference")


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
        description="Strategic public services and landmarks matching the inquiry."
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
# DETERMINISTIC FALLBACK ENGINE WITH VERIFIED DIRECTORY
# ==============================================================================
def _deterministic_fallback(message: str) -> Dict[str, Any]:
    """Provide high-fidelity cultural responses, schedule, route, and verified directory points."""
    msg = message.lower().strip()
    schedule_data = get_schedule_for_query(message)

    # Filter categories helper
    def get_by_category(cat: str) -> List[Dict[str, Any]]:
        return [p for p in PASTO_PLACES_DIRECTORY if p["category"] == cat]

    # Case 1: Baños Públicos
    if any(k in msg for k in ["baño", "baños", "sanitario", "sanitarios", "batería", "bateria", "orinar", "chichi", "restroom"]):
        bathrooms = get_by_category("restroom")
        return {
            "reply": (
                "¡A la orden, veci! Para que no pase apuros durante el jolgorio, en San Juan de Pasto cuenta con 4 baterías de baños públicos verificadas:\n"
                "1. **Batería San Agustín**: Calle 19 con Cra 24 [1.2138, -77.2779] (Abierta de 8:00 AM a 9:00 PM con personal de aseo).\n"
                "2. **Baños Plaza del Carnaval**: En el parqueadero subterráneo de la plaza [1.2132, -77.2783] (Servicio continuo con amplias cabinas).\n"
                "3. **Baños Estadio Libertad**: Costado Occidental del estadio [1.2028, -77.2765] (Habilitados desde las 7:00 AM para la partida del desfile).\n"
                "4. **Baños Plaza de Nariño**: Casa de Don Lorenzo en Carrera 26 con Calle 19 [1.2149, -77.2783] (Abiertos de 8:00 AM a 10:00 PM).\n"
                "¡Ya se los dejo todos fijados en el mapa con sus direcciones exactas!"
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": [[p["coordinates"][0], p["coordinates"][1]] for p in bathrooms],
            "waypoints": [[p["coordinates"][0], p["coordinates"][1]] for p in bathrooms],
            "nearby_places": bathrooms,
            "suggested_questions": [
                "¿Dónde queda el puesto de salud más cercano?",
                "¿Cuál es el recorrido oficial de la Senda del Carnaval?",
                "¿Dónde puedo comer un buen cuy asado?"
            ]
        }

    # Case 2: Seguridad / CAIs
    if any(k in msg for k in ["policia", "policía", "cai", "seguridad", "denuncia", "robo", "perdido"]):
        cais = get_by_category("police")
        return {
            "reply": (
                "¡Tranquilo, paisano! La seguridad del Carnaval cuenta con puestos policiales CAI activos las 24 horas a lo largo del recorrido:\n"
                "1. **CAI Plaza de Nariño**: En el Centro Histórico, esquina noroccidental de la plaza [1.2144, -77.2788] (Atención de cuadrante y extravíos).\n"
                "2. **CAI Lorenzo de Aldana**: En la Glorieta Lorenzo con Carrera 4 [1.2092, -77.2768] (Vigilancia del sector sur y concentración inicial).\n"
                "3. **CAI Morasurco**: Entrada Norte sobre la Avenida Santander [1.2298, -77.2835] (Apoyo en la llegada a Torobajo y Av. de los Estudiantes).\n"
                "Recomendación carnavalera: mantenga sus pertenencias en bolsillos frontales con cremallera y proteja a los niños."
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": [[p["coordinates"][0], p["coordinates"][1]] for p in cais],
            "waypoints": [[p["coordinates"][0], p["coordinates"][1]] for p in cais],
            "nearby_places": cais,
            "suggested_questions": [
                "¿Cuáles son las zonas de mayor aglomeración de gente?",
                "¿Dónde quedan los puestos de primeros auxilios de la Cruz Roja?",
                "¿A qué hora empieza el Desfile Magno del 6 de enero?"
            ]
        }

    # Case 3: Salud / Cruz Roja / Primeros Auxilios / Hospital
    if any(k in msg for k in ["salud", "cruz roja", "primeros auxilios", "ambulancia", "hospital", "médico", "medico", "emergencia"]):
        health_spots = get_by_category("health")
        return {
            "reply": (
                "¡Para servirle, veci! La red de socorro y atención prehospitalaria está lista en los siguientes puntos estratégicos:\n"
                "1. **Puesto Cruz Roja Plaza Carnaval**: Esquina Carrera 27 [1.2130, -77.2781] (Carpa de triage, ambulancia medicalizada y voluntarios de 8:00 AM a 11:00 PM).\n"
                "2. **Puesto Defensa Civil San Felipe**: Calle 18 con Carrera 27 [1.2180, -77.2800] (Primeros auxilios e hidratación durante el desfile).\n"
                "3. **Hospital Departamental de Nariño**: Calle 16 # 27-02 [1.2080, -77.2750] (Servicio de urgencias de tercer nivel 24 horas).\n"
                "¡Use gafas protectoras contra el talco y carioca, y tome abundante agüita!"
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": [[p["coordinates"][0], p["coordinates"][1]] for p in health_spots],
            "waypoints": [[p["coordinates"][0], p["coordinates"][1]] for p in health_spots],
            "nearby_places": health_spots,
            "suggested_questions": [
                "¿Dónde quedan los baños cerca a la Plaza del Carnaval?",
                "¿Cómo llegar a la Avenida de los Estudiantes?",
                "¿Dónde comprar gafas y ponchos protectores?"
            ]
        }

    # Case 4: Restaurantes / Cafés / Gastronomía Típica
    if any(k in msg for k in ["restaurante", "comer", "comida", "cuy", "gastronomia", "gastronomía", "cafe", "café", "almorzar", "empanada"]):
        restaurants = get_by_category("restaurant")
        return {
            "reply": (
                "¡Uyyyy qué delicia, veci! Si de comer sabroso se trata en Pasto, aquí tiene los sitios recomendados en el trayecto:\n"
                "1. **Restaurante El Paisano / Asadero**: Sector San Felipe, Calle 18 # 26-45 [1.2190, -77.2802] (El mejor cuy asado tradicional con papas pastusas, crispetas y ají de maní).\n"
                "2. **Cafetería La Merced**: Calle 18 cerca a la Plaza de Nariño [1.2150, -77.2786] (Famosa por sus quimbolitos recién hechos, empanadas de añejo y café nariñense).\n"
                "3. **Zona Gastronómica Avenida de los Estudiantes**: Entre Calles 19 y 22 [1.2270, -77.2828] (Corredor de asaderos, comidas rápidas y piqueteaderos abiertos durante todo el desfile)."
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": [[p["coordinates"][0], p["coordinates"][1]] for p in restaurants],
            "waypoints": [[p["coordinates"][0], p["coordinates"][1]] for p in restaurants],
            "nearby_places": restaurants,
            "suggested_questions": [
                "¿Cuánto cuesta un plato de cuy típico en Pasto?",
                "¿Dónde queda la Tarima Oficial de orquestas?",
                "¿Cuál es el recorrido de la Senda del Carnaval?"
            ]
        }

    # Case 5: Tarimas / Conciertos / Música
    if any(k in msg for k in ["tarima", "tarimas", "musica", "música", "concierto", "conciertos", "orquesta", "escenario", "baile"]):
        stages = get_by_category("stage")
        return {
            "reply": (
                "¡A bailar y a gozar con la Guaneña, paisano! Las tres tarimas oficiales del Carnaval están confirmadas:\n"
                "1. **Tarima Oficial Plaza del Carnaval**: Plaza del Carnaval y la Cultura [1.2136, -77.2785] (Escenario principal de orquestas nacionales e internacionales y murgas).\n"
                "2. **Tarima de la Danza y Tradición Plaza de Nariño**: Centro Histórico [1.2148, -77.2780] (Música autóctona, zampoñas, charangos y grupos de danza andina).\n"
                "3. **Tarima del Carrizal**: Avenida Mijitayo [1.2225, -77.2815] (Escenario de son sureño, música campesina y bandas juveniles)."
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": [[p["coordinates"][0], p["coordinates"][1]] for p in stages],
            "waypoints": [[p["coordinates"][0], p["coordinates"][1]] for p in stages],
            "nearby_places": stages,
            "suggested_questions": [
                "¿A qué hora empiezan las orquestas en la Plaza del Carnaval?",
                "¿Dónde quedan los baños en la Plaza de Nariño?",
                "¿Qué artistas se presentan en la Tarima de Nariño?"
            ]
        }

    # Case 6: Recorrido Completo de la Senda
    if any(k in msg for k in ["senda", "recorrido", "ruta", "trayecto", "camino", "desfile"]):
        return {
            "reply": (
                "¡Qué viva Pasto, carajo, veci! Aquí le tengo el trazado calle a calle con máxima precisión de la Senda del Carnaval:\n"
                "• **Partida**: Estadio Departamental Libertad [1.2025, -77.2762].\n"
                "• **Subida**: Calle 2 / Carrera 4 hasta la Glorieta Lorenzo de Aldana [1.2095, -77.2770].\n"
                "• **Bajada**: Calle 19 pasando por la emblemática Plaza del Carnaval [1.2136, -77.2785].\n"
                "• **Giro céntrico**: Carrera 27 pasando junto a la Plaza de Nariño [1.2148, -77.2780].\n"
                "• **Tramo norte**: Subida por Calle 18 hasta San Felipe [1.2220, -77.2810], conectando con Carrera 40 y la Avenida de los Estudiantes.\n"
                "• **Llegada**: Fuente de la Transparencia / Glorieta Torobajo [1.2330, -77.2845].\n"
                "¡Son cerca de 7 kilómetros de emoción! Además le incluyo en el mapa todos los baños, puestos de auxilio y CAIs de policía."
            ),
            "schedule": schedule_data,
            "should_draw_route": True,
            "route_coordinates": SENDA_OFFICIAL_PATH,
            "waypoints": SENDA_OFFICIAL_PATH,
            "nearby_places": PASTO_PLACES_DIRECTORY,
            "suggested_questions": [
                "¿Dónde quedan los baños públicos en la ruta?",
                "¿Dónde están ubicados los puestos de la Cruz Roja?",
                "¿A qué hora arranca el desfile del 6 de enero?"
            ]
        }

    # Default friendly Pastuso response
    return {
        "reply": (
            "¡Qué viva Pasto, carajo, veci! Soy GuaneñaBot, su guía oficial del Carnaval de Negros y Blancos. "
            "Le tengo el mapa exacto calle a calle de la Senda del Carnaval y el directorio completo de Pasto con ubicaciones verificadas: "
            "baños públicos (🚻), puestos de salud de la Cruz Roja (🚑), CAIs de policía (👮), restaurantes típicos de cuy (🍴) "
            "y tarimas musicales (🎪). ¿Qué punto o evento desea consultar?"
        ),
        "schedule": schedule_data,
        "should_draw_route": True,
        "route_coordinates": SENDA_OFFICIAL_PATH,
        "waypoints": SENDA_OFFICIAL_PATH,
        "nearby_places": PASTO_PLACES_DIRECTORY,
        "suggested_questions": [
            "¿Dónde quedan los baños públicos autorizados?",
            "¿Dónde puedo comer cuy típico cerca a la Senda?",
            "¿Cuál es el recorrido exacto de la Senda del Carnaval?"
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
        Dict matching CarnavalChatResponse schema with schedule, route, and verified nearby places.
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

Please respond according to your persona and structured JSON schema including schedule, route_coordinates, and verified nearby_places with address.
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
                    nearby_places = PASTO_PLACES_DIRECTORY

                return {
                    "reply": data.get("reply", "¡Qué viva Pasto, carajo!"),
                    "schedule": schedule_obj,
                    "should_draw_route": bool(data.get("should_draw_route", False)),
                    "route_coordinates": route_coords,
                    "waypoints": route_coords,
                    "nearby_places": nearby_places,
                    "suggested_questions": data.get("suggested_questions", [
                        "¿Dónde quedan los baños públicos autorizados?",
                        "¿Dónde puedo comer cuy típico cerca a la Senda?",
                        "¿Cuál es el recorrido exacto de la Senda del Carnaval?"
                    ])
                }
        except Exception as exc:
            logger.warning(
                f"[GEMINI_SERVICE] Notice while querying Gemini 2.5 Flash ({type(exc).__name__}: {exc}). "
                "Engaging deterministic cultural GIS fallback."
            )

    # Deterministic fallback when Gemini API is unavailable or offline
    return _deterministic_fallback(message)
