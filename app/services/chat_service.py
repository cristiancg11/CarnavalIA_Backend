"""Servicio de Asistente Virtual IA con RAG Contextual para el Carnaval de Negros y Blancos de Pasto.

Integra Google Gemini (gemini-2.5-flash) con contexto dinámico de:
1. Base de datos cultural oficial del Carnaval de San Juan de Pasto (28-dic a 07-ene).
2. Restaurantes conocidos y gastronomía tradicional nariñense con geolocalización y cálculo de proximidad.
3. Formato estructurado JSON con 'reply' y 'action' ({ "type": "ROUTE", "target_name", "target_coords" }).
4. Puntos de interés en vivo (Salud, Policía, Tarimas, Baños) y reportes ciudadanos activos.
"""
import json
import logging
import math
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from app.core.config import settings
from app.models.point_of_interest import PointOfInterest
from app.models.report import Report
from app.models.zone_risk import ZoneRisk
from app.schemas.chat import ChatResponse

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. BASE DE DATOS CULTURAL DEL CARNAVAL DE PASTO (28 Dic - 07 Ene)
# ==============================================================================
CARNIVAL_SCHEDULE_DATA: Dict[str, Dict[str, Any]] = {
    "28-dic": {
        "name": "Arcoíris en el Asfalto - El Colorado",
        "date_label": "28 de Diciembre",
        "hours": "08:00 - 18:00",
        "description": "Pintura artística con tiza sobre el asfalto. Celebración cultural por la paz, el arte urbano y el cuidado del agua.",
        "closed_points": [
            "Cra 23 entre Calles 14 y 15 (Sector El Colorado)",
            "Calle 16 entre Cra 23 y Cra 27"
        ],
        "notes": "Zona céntrica totalmente peatonal para artistas, niños y familias."
    },
    "31-dic": {
        "name": "Años Viejos - Senda Cra 27",
        "date_label": "31 de Diciembre",
        "hours": "08:00 - 16:00",
        "description": "Desfile de Años Viejos y Viudas. Humor, sátira política, testamentos y quema simbólica de monigotes.",
        "start": "Salida: Escuela Normal Superior / Transversal del Caracha",
        "end": "Llegada: Sector Champagnat (IEM Ciudad de Pasto)",
        "closed_points": [
            "Bloqueo Caracha / Cra 27",
            "Cierre Calle 19 y acceso Plaza de Nariño",
            "Desconcentración Champagnat"
        ],
        "notes": "Cierre escalonado en el eje de la Carrera 27 hacia el norte."
    },
    "02-ene": {
        "name": "Carnavalito",
        "date_label": "02 de Enero",
        "hours": "07:00 - 14:00",
        "description": "Desfile infantil con mini-carrozas, comparsitas y devoción tradicional a la Virgen de las Mercedes.",
        "start": "Salida: Escuela Normal Superior",
        "end": "Llegada: Sector Champagnat",
        "closed_points": [
            "Cierre Cra 27 sur-norte",
            "Cierre Calle 19 (Plaza Nariño)"
        ],
        "notes": "Gran afluencia de niños; se recomienda especial cuidado y puntos de encuentro fijos."
    },
    "03-ene": {
        "name": "Canto a la Tierra",
        "date_label": "03 de Enero",
        "hours": "09:00 - 16:00",
        "description": "Desfile de Colectivos Coreográficos. Miles de músicos y danzantes andinos con zampoñas, bombos, quenas y trajes multicolores.",
        "start": "Salida: Escuela Normal Superior",
        "end": "Llegada: Sector Champagnat",
        "closed_points": [
            "Cierre total Carrera 27",
            "Cierre Calle 19",
            "Restricción cruces Av. Los Estudiantes"
        ],
        "notes": "Sonoridad andina ininterrumpida a lo largo de toda la senda de la Cra 27."
    },
    "04-ene": {
        "name": "Familia Castañeda",
        "date_label": "04 de Enero",
        "hours": "08:00 - 15:00",
        "description": "Llegada de la Familia Castañeda. Teatro callejero, carretas de época y bienvenida festiva recreando la comitiva campesina de 1929.",
        "start": "Salida: Escuela Normal Superior",
        "end": "Llegada: Sector Champagnat",
        "closed_points": [
            "Cierre total Carrera 27",
            "Cierre Calle 19 y Plaza de Nariño"
        ],
        "notes": "¡Atención! El centro histórico y la Plaza de Nariño quedan 100% peatonalizados. Prohibido el tráfico vehicular en todo el anillo central."
    },
    "05-ene": {
        "name": "Día de Negros - Juego de pintica y tarimas",
        "date_label": "05 de Enero",
        "hours": "11:00 - 23:00",
        "description": "Conmemoración de la libertad y la igualdad étnica; juego fraterno con cosmético negro, orquestas en vivo y tarimas musicales. (No hay desfile de carrozas monumentales).",
        "closed_points": [
            "Peatonalización Plaza del Carnaval",
            "Peatonalización Plaza de Nariño",
            "Zona de Graderías controladas (San Juan Bosco)"
        ],
        "notes": "Las plazas principales se convierten en gigantescas tarimas y áreas peatonales festivas."
    },
    "06-ene": {
        "name": "Día de Blancos - Desfile Magno de Carrozas",
        "date_label": "06 de Enero",
        "hours": "05:00 - 17:00",
        "description": "La cumbre del Carnaval: Majestuosas Carrozas Monumentales de hasta 12m de altura, comparsas, murgas, juego con talco perfumado y carioca.",
        "start": "Salida: Avenida Emmanuel (Tamasagra / Anganoy)",
        "end": "Llegada: Avenida Alfonso Zambrano (Estadio Libertad)",
        "closed_points": [
            "Cierre Av. Emmanuel desde las 5:00 AM",
            "Cierre Avenida Mijitayo",
            "Corte cruce Av. Panamericana",
            "Cierre Carrera 27",
            "Cierre Calle 19",
            "Cierre Av. Alfonso Zambrano"
        ],
        "notes": "Cierres masivos en la ciudad desde la madrugada. Máxima concentración de público. Usar gafas protectoras."
    },
    "07-ene": {
        "name": "Festival del Cuy en Obonuco y Catambuco",
        "date_label": "07 de Enero",
        "hours": "09:00 - 17:00",
        "description": "Festival del Cuy y la Cultura Campesina. Gastronomía autóctona, música campesina, remate del Carnaval en los corregimientos.",
        "closed_points": [
            "Cierre plaza corregimiento de Obonuco",
            "Cierre plaza corregimiento de Catambuco"
        ],
        "notes": "Vías urbanas despejadas; la fiesta se traslada a los corregimientos rurales de Obonuco y Catambuco."
    }
}

# ==============================================================================
# 2. LISTA DE RESTAURANTES CONOCIDOS DE PASTO
# ==============================================================================
PASTO_RESTAURANTS_DATA: List[Dict[str, Any]] = [
    {
        "name": "Cuyquer",
        "sector": "Mijitayo",
        "latitude": 1.2160,
        "longitude": -77.2915,
        "hours": "11:30 - 18:00",
        "specialty": "Cuy Asado tradicional",
        "description": "Tradicional asadero de cuy con preparaciones ancestrales nariñenses, ají de maní y papas al vapor."
    },
    {
        "name": "El Rincón del Cuy",
        "sector": "Av. Mijitayo / Panamericana",
        "latitude": 1.2140,
        "longitude": -77.2870,
        "hours": "11:00 - 19:00",
        "specialty": "Cuy asado al carbón",
        "description": "Especialistas en cuy asado al carbón en vara tradicional, frito pastuso y caldo de pajarilla."
    },
    {
        "name": "Café San Sebastián",
        "sector": "Centro Histórico",
        "latitude": 1.2142,
        "longitude": -77.2795,
        "hours": "08:00 - 21:00",
        "specialty": "Café especial de Nariño y pasabocas",
        "description": "Café de origen de alta montaña, repostería artesanal, quimbolitos y ambiente cultural del centro."
    },
    {
        "name": "La Cabaña Andina",
        "sector": "Plaza Nariño",
        "latitude": 1.2145,
        "longitude": -77.2780,
        "hours": "07:30 - 20:30",
        "specialty": "Empanadas de añejo y café nariñense",
        "description": "Ícono del centro histórico junto a la Plaza de Nariño. Famosas empanadas de añejo crocantes con pipián, ají y café."
    },
    {
        "name": "Parrilla Gourmet",
        "sector": "Carrera 27 - Senda",
        "latitude": 1.2125,
        "longitude": -77.2770,
        "hours": "12:00 - 22:00",
        "specialty": "Carnes a la brasa y almuerzos",
        "description": "Cortes seleccionados a la parrilla, almuerzos ejecutivos y vista directa al paso de los desfiles."
    },
    {
        "name": "Asadero La Merced",
        "sector": "Salida Obonuco",
        "latitude": 1.1890,
        "longitude": -77.2920,
        "hours": "10:30 - 18:00",
        "specialty": "Cuy campesino y platos autóctonos",
        "description": "Ambiente campestre en la ruta tradicional hacia Obonuco. Cuy entero asado, envueltos y chicha tradicional."
    }
]

# Mapa rápido para georreferenciación de rutas
KNOWN_LOCATIONS: Dict[str, Tuple[str, List[float]]] = {
    "cuyquer": ("Cuyquer en Mijitayo", [1.2160, -77.2915]),
    "rincon del cuy": ("El Rincón del Cuy", [1.2140, -77.2870]),
    "el rincon del cuy": ("El Rincón del Cuy", [1.2140, -77.2870]),
    "rincón del cuy": ("El Rincón del Cuy", [1.2140, -77.2870]),
    "el rincón del cuy": ("El Rincón del Cuy", [1.2140, -77.2870]),
    "cafe san sebastian": ("Café San Sebastián en Centro", [1.2142, -77.2795]),
    "café san sebastián": ("Café San Sebastián en Centro", [1.2142, -77.2795]),
    "san sebastian": ("Café San Sebastián en Centro", [1.2142, -77.2795]),
    "san sebastián": ("Café San Sebastián en Centro", [1.2142, -77.2795]),
    "la cabaña andina": ("La Cabaña Andina en Plaza Nariño", [1.2145, -77.2780]),
    "cabaña andina": ("La Cabaña Andina en Plaza Nariño", [1.2145, -77.2780]),
    "la cabana andina": ("La Cabaña Andina en Plaza Nariño", [1.2145, -77.2780]),
    "cabana andina": ("La Cabaña Andina en Plaza Nariño", [1.2145, -77.2780]),
    "plaza de nariño": ("Plaza de Nariño", [1.2145, -77.2780]),
    "plaza nariño": ("Plaza de Nariño", [1.2145, -77.2780]),
    "plaza de narino": ("Plaza de Nariño", [1.2145, -77.2780]),
    "plaza narino": ("Plaza de Nariño", [1.2145, -77.2780]),
    "plaza del carnaval": ("Plaza del Carnaval y la Cultura", [1.2115, -77.2765]),
    "el colorado": ("El Colorado (Cra 23)", [1.2150, -77.2820]),
    "obonuco": ("Corregimiento de Obonuco", [1.1890, -77.2920]),
    "catambuco": ("Corregimiento de Catambuco", [1.1710, -77.2850]),
    "champagnat": ("Sector Champagnat", [1.2190, -77.2740]),
    "normal superior": ("Escuela Normal Superior", [1.2050, -77.2830]),
}

# ==============================================================================
# 3. ESQUEMA PYDANTIC PARA RESPUESTA ESTRUCTURADA DE GEMINI
# ==============================================================================
class ActionPayload(BaseModel):
    """Acción de control para el mapa interactivo (SET_DAY o ROUTE)."""
    type: str = Field(description="Tipo de acción: 'SET_DAY' o 'ROUTE'")
    # Campos para acción SET_DAY (control dinámico del mapa por fecha)
    day_key: Optional[str] = Field(
        default=None,
        description="Clave del día del carnaval: '28-dic', '31-dic', '02-ene', '03-ene', '04-ene', '05-ene', '06-ene', '07-ene'"
    )
    event_title: Optional[str] = Field(
        default=None,
        description="Título descriptivo del evento o desfile oficial"
    )
    # Campos para acción ROUTE (navegación a pie hacia un sitio)
    target_name: Optional[str] = Field(
        default=None,
        description="Nombre del sitio o restaurante de destino"
    )
    target_coords: Optional[List[float]] = Field(
        default=None,
        description="Coordenadas [latitud, longitud] del destino"
    )


class StructuredChatResponse(BaseModel):
    """Esquema JSON obligatorio que retorna el modelo de Gemini."""
    reply: str = Field(..., description="Texto festivo nariñense respondiendo la duda exacta.")
    action: Optional[ActionPayload] = Field(
        default=None,
        description="Objeto de acción si el usuario consulta una fecha del Carnaval ('SET_DAY') o pide ruta ('ROUTE'), o null si no aplica."
    )


# ==============================================================================
# 4. CONSTRUCTOR DE SYSTEM PROMPT DINÁMICO
# ==============================================================================
def build_dynamic_system_prompt(selected_day: Optional[str] = None) -> str:
    """Construye las instrucciones de sistema dinámicas para Gemini:

    - Sin textos fijos que obliguen a responder sobre el 5 de enero.
    - Base de datos cultural completa (28 Dic a 07 Ene).
    - Lista de restaurantes conocidos de Pasto con coordenadas.
    - Estricto formato de respuesta JSON estructurado: { "reply": "...", "action": null / ROUTE }.
    """
    context_day_instruction = (
        f"El usuario tiene actualmente seleccionado en el mapa de la app el día '{selected_day}'. "
        "Si pregunta de forma abierta ('¿qué hay hoy?', '¿qué desfile hay ahora?'), utiliza este día como referencia. "
        "Si el usuario pregunta por otra fecha o realiza una pregunta gastronómica, de salud o general, "
        "responde directamente a su consulta sin forzar el día seleccionado."
        if selected_day
        else "No hay ningún día fijado por defecto. Responde dinámicamente según la duda concreta del usuario sin asumir una fecha fija."
    )

    return f"""Eres el Asistente Virtual Oficial con Inteligencia Artificial del Carnaval de Negros y Blancos de San Juan de Pasto, declarado Patrimonio Cultural Inmaterial de la Humanidad por la UNESCO.
Tu misión principal es orientar, acompañar, informar y salvaguardar a propios y turistas con información precisa, contextualizada y en tiempo real.

Personalidad y Tono:
- Hospitalario, alegre, festivo, empático, protector y orgulloso de las tradiciones nariñenses ("¡Que viva Pasto, Carajo!").
- Emplea con calidez y naturalidad expresiones nariñenses ("paisano", "guagua", "a la orden", "¡caray!").
- Enérgico, respetuoso y fidedigno con las fechas, calles y gastronomía de Pasto.
- DINÁMICO: Responde exactamente a lo que consulte el usuario. NO fuerces respuestas sobre un día fijo (como el 5 de enero) a menos que el usuario lo consulte explícitamente.

Directriz de Contexto Dinámico:
{context_day_instruction}

Base de Datos Cultural del Carnaval de Pasto:
* 28 Dic (Arcoíris en el Asfalto - El Colorado): Pintura artística con tiza sobre el asfalto, celebración por la paz y el agua en la Cra 23 entre Calles 14 y 15.
* 31 Dic (Años Viejos - Senda Cra 27): Desfile de monigotes, viudas, humor, sátira y quema simbólica desde la Normal Superior hasta Champagnat.
* 02 Ene (Carnavalito): Desfile infantil con mini-carrozas y comparsitas; ofrenda y devoción a la Virgen de las Mercedes.
* 03 Ene (Canto a la Tierra): Desfile de Colectivos Coreográficos, miles de músicos y danzantes andinos con quenas, zampoñas y bombos por la Cra 27.
* 04 Ene (Familia Castañeda): Llegada de la comitiva campesina de 1929 con teatro callejero y cuadros de época; centro histórico 100% peatonalizado.
* 05 Ene (Día de Negros - Juego de pintica y tarimas): Juego fraterno con cosmético negro, orquestas y tarimas en Plaza del Carnaval y Plaza de Nariño; no hay desfile de carrozas monumentales.
* 06 Ene (Día de Blancos - Desfile Magno de Carrozas): Máxima expresión artística con Carrozas Monumentales de hasta 12m, comparsas, murgas, talco perfumado y carioca a lo largo de toda la Senda.
* 07 Ene (Festival del Cuy en Obonuco y Catambuco): Gastronomía autóctona campesina, concurso del mejor cuy, música tradicional y remate en corregimientos.

Lista de Restaurantes Conocidos de Pasto:
* Cuyquer en Mijitayo [1.2160, -77.2915]: Tradicional asadero de cuy con preparaciones ancestrales, ají de maní y papas al vapor.
* El Rincón del Cuy [1.2140, -77.2870]: Ubicado en Av. Mijitayo / Panamericana, expertos en cuy asado al carbón en vara tradicional y frito pastuso.
* Café San Sebastián en Centro [1.2142, -77.2795]: Ubicado en el Centro Histórico, café especial de origen nariñense de alta montaña, repostería y quimbolitos.
* La Cabaña Andina en Plaza Nariño [1.2145, -77.2780]: Ícono junto a la Plaza de Nariño, famosas empanadas de añejo crocantes con pipián y café nariñense.

Control Dinámico del Mapa y Formato de Respuesta:
Debes responder SIEMPRE con un objeto JSON estructurado con los campos "reply" y "action":

1. Si el usuario pregunta o menciona una fecha del Carnaval (ej: "28 de diciembre", "31 de diciembre", "2 de enero", "3 de enero", "4 de enero", "5 de enero", "6 de enero", "7 de enero" o nombres de desfiles como "Carrozas", "Familia Castañeda", "Años Viejos", "Canto a la Tierra", "Carnavalito"):
   - Explica con entusiasmo y detalle qué se celebra, qué verá el turista, los horarios oficiales y los cierres viales.
   - En el campo "action", DEBES emitir OBLIGATORIAMENTE una acción de tipo "SET_DAY" para que la app cambie automáticamente el mapa, la senda y los cierres viales:
     {{
       "type": "SET_DAY",
       "day_key": "06-ene",
       "event_title": "Día de Blancos - Desfile Magno"
     }}
     (Utiliza exactamente la clave correspondiente: '28-dic', '31-dic', '02-ene', '03-ene', '04-ene', '05-ene', '06-ene', '07-ene').

2. Si el usuario solicita una ruta, indicaciones para llegar, cómo ir o dónde queda un restaurante o sitio específico:
   - En el campo "action", emite una acción de tipo "ROUTE":
     {{
       "type": "ROUTE",
       "target_name": "Nombre exacto del restaurante o sitio",
       "target_coords": [latitud, longitud]
     }}

3. Si no mencionan fecha del Carnaval ni solicitan ruta hacia un punto, "action" debe ser null:
     {{
       "reply": "Texto festivo nariñense respondiendo la duda exacta",
       "action": null
     }}
"""


# ==============================================================================
# 5. UTILIDADES GEOGRÁFICAS Y PARSEO
# ==============================================================================
def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia geodésica en kilómetros entre dos coordenadas usando Haversine."""
    earth_radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_km * c


def _format_distance(km: float) -> str:
    """Formatea una distancia en metros o kilómetros para fácil lectura."""
    meters = km * 1000.0
    if meters < 1000.0:
        return f"{int(round(meters))} metros"
    return f"{km:.2f} km"


def is_restaurant_open_now(hours_str: str) -> bool:
    """Calcula si un restaurante está abierto comparando la hora actual con su rango."""
    try:
        now = datetime.now()
        cur_min = now.hour * 60 + now.minute
        parts = hours_str.split("-")
        if len(parts) == 2:
            s_h, s_m = map(int, parts[0].strip().split(":"))
            e_h, e_m = map(int, parts[1].strip().split(":"))
            return (s_h * 60 + s_m) <= cur_min <= (e_h * 60 + e_m)
    except Exception:
        pass
    return False


def _clean_and_parse_json(text: str) -> Dict[str, Any]:
    """Limpia bloques de código markdown y parsea un texto JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    return json.loads(cleaned)


DAY_DETECTION_PATTERNS = [
    ("28-dic", "28 de Diciembre - Arcoíris en el Asfalto", ["28 de dic", "28 dic", "arcoiris", "arcoíris", "colorado"]),
    ("31-dic", "31 de Diciembre - Desfile de Años Viejos", ["31 de dic", "31 dic", "año viejo", "años viejos", "viudas"]),
    ("02-ene", "02 de Enero - Carnavalito", ["2 de ene", "02 de ene", "2 ene", "02 ene", "carnavalito"]),
    ("03-ene", "03 de Enero - Canto a la Tierra", ["3 de ene", "03 de ene", "3 ene", "03 ene", "canto a la tierra", "colectivos"]),
    ("04-ene", "04 de Enero - Llegada de la Familia Castañeda", ["4 de ene", "04 de ene", "4 ene", "04 ene", "castañeda", "castaneda"]),
    ("05-ene", "05 de Enero - Día de Negros", ["5 de ene", "05 de ene", "5 ene", "05 ene", "día de negros", "dia de negros", "juego de pintica", "pintica"]),
    ("06-ene", "06 de Enero - Día de Blancos (Desfile Magno)", ["6 de ene", "06 de ene", "6 ene", "06 ene", "día de blancos", "dia de blancos", "desfile magno", "carrozas"]),
    ("07-ene", "07 de Enero - Festival del Cuy y la Cultura Campesina", ["7 de ene", "07 de ene", "7 ene", "07 ene", "festival del cuy", "obonuco", "catambuco"]),
]


def _detect_requested_day(query: str) -> Optional[Dict[str, Any]]:
    """Detecta si la consulta del usuario hace referencia a un día del Carnaval de Pasto."""
    q = query.lower()
    for day_key, default_title, keywords in DAY_DETECTION_PATTERNS:
        if any(kw in q for kw in keywords):
            title = CARNIVAL_SCHEDULE_DATA.get(day_key, {}).get("name", default_title)
            return {
                "type": "SET_DAY",
                "day_key": day_key,
                "event_title": title
            }
    return None


def _detect_requested_route(query: str) -> Optional[Dict[str, Any]]:
    """Detecta si la consulta del usuario pide una ruta o llegar a un destino conocido."""
    q = query.lower()
    wants_route = any(w in q for w in [
        "cómo llegar", "como llegar", "cómo llego", "como llego", "llegar a", "llego a",
        "ruta", "cómo voy", "como voy", "ir a", "guíame", "guiame",
        "dónde queda", "donde queda", "dónde está", "donde esta", "dónde encuentro", "donde encuentro"
    ])
    if not wants_route:
        return None

    for key, (name, coords) in KNOWN_LOCATIONS.items():
        if key in q:
            return {
                "type": "ROUTE",
                "target_name": name,
                "target_coords": coords
            }
    return None


# ==============================================================================
# 6. CONSTRUCCIÓN DE CONTEXTO RAG
# ==============================================================================
def build_full_rag_context(
    db: Optional[Session] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    selected_day: Optional[str] = None
) -> Tuple[str, List[str]]:
    """Construye el contexto integral en tiempo real:

    - Cronograma oficial y cierres viales (sin forzar días estáticos).
    - Restaurantes conocidos de Pasto con proximidad y estado abierto/cerrado.
    - Puntos de interés y reportes ciudadanos activos desde la base de datos.
    """
    sources_used: List[str] = []
    context_sections: List[str] = []

    has_location = user_lat is not None and user_lon is not None
    if has_location:
        sources_used.append(f"Geolocalización GPS activa: Lat {user_lat:.4f}, Lon {user_lon:.4f}")

    # 1. Día Seleccionado en la App (solo si fue explícitamente seleccionado)
    if selected_day and selected_day in CARNIVAL_SCHEDULE_DATA:
        day_info = CARNIVAL_SCHEDULE_DATA[selected_day]
        sources_used.append(f"Agenda Oficial Carnaval: Día activo '{selected_day}' ({day_info['name']})")
        day_text = (
            f"DÍA ACTUALMENTE SELECCIONADO EN EL MAPA: {selected_day} - {day_info['name']}\n"
            f"• Horario Oficial: {day_info['hours']}\n"
            f"• Descripción: {day_info['description']}\n"
        )
        if "start" in day_info:
            day_text += f"• Salida: {day_info['start']}\n"
        if "end" in day_info:
            day_text += f"• Llegada: {day_info['end']}\n"
        day_text += "• Puntos de Cierre Vial activos hoy:\n"
        for cp in day_info["closed_points"]:
            day_text += f"  - ⛔ {cp}\n"
        if "notes" in day_info:
            day_text += f"• Indicación logística: {day_info['notes']}\n"
        context_sections.append(day_text)

    # 2. Resumen Completo de Todos los Días del Carnaval para RAG Dinámico
    all_days_summary = ["BASE DE DATOS CULTURAL Y CIERRES VIALES (28 Dic - 07 Ene):"]
    for day_id, d in CARNIVAL_SCHEDULE_DATA.items():
        all_days_summary.append(
            f"[{day_id}] {d['name']} ({d['hours']}): {d['description']}. "
            f"Cierres: {', '.join(d['closed_points'])}. {d.get('notes', '')}"
        )
    context_sections.append("\n".join(all_days_summary))

    # 3. Restaurantes Conocidos de Pasto (con cálculo de proximidad si hay GPS)
    restaurant_entries = []
    sorted_restaurants = []
    for r in PASTO_RESTAURANTS_DATA:
        dist_km = None
        if has_location:
            dist_km = _haversine_distance_km(user_lat, user_lon, r["latitude"], r["longitude"])
        is_open = is_restaurant_open_now(r["hours"])
        sorted_restaurants.append((r, dist_km, is_open))

    if has_location:
        sorted_restaurants.sort(key=lambda x: x[1] if x[1] is not None else float("inf"))

    for r, dist, is_open in sorted_restaurants:
        status_str = "🟢 ABIERTO AHORA" if is_open else "🔴 CERRADO"
        dist_str = f" | Distancia desde tu ubicación: {_format_distance(dist)}" if dist is not None else ""
        restaurant_entries.append(
            f"- 🍽️ {r['name']} ({r['sector']}) [{status_str} | Horario: {r['hours']}]{dist_str}\n"
            f"  Especialidad: {r['specialty']}. {r['description']} [Coords: {r['latitude']}, {r['longitude']}]"
        )

    context_sections.append("RESTAURANTES CONOCIDOS Y GASTRONOMÍA TRADICIONAL DE PASTO:\n" + "\n".join(restaurant_entries))
    sources_used.append(f"Directorio Gastronómico: {len(PASTO_RESTAURANTS_DATA)} restaurantes de Pasto")

    # 4. Puntos de Interés en BD (Salud, Policía, Tarimas, Baños)
    if db is not None:
        try:
            pois = db.query(PointOfInterest).all()
            if pois:
                poi_items = []
                for poi in pois:
                    dist_km = None
                    if has_location:
                        dist_km = _haversine_distance_km(user_lat, user_lon, poi.latitude, poi.longitude)
                    poi_items.append((poi, dist_km))

                if has_location:
                    poi_items.sort(key=lambda x: x[1] if x[1] is not None else float("inf"))

                poi_entries = []
                for poi, dist in poi_items:
                    dist_str = f" - Distancia: {_format_distance(dist)}" if dist is not None else ""
                    poi_entries.append(
                        f"- [{poi.category.upper()}] {poi.name} ({poi.description or 'Servicio oficial'}){dist_str} [Coords: {poi.latitude}, {poi.longitude}]"
                    )

                context_sections.append("PUNTOS DE SALUD, SEGURIDAD Y TARIMAS:\n" + "\n".join(poi_entries))
                sources_used.append(f"Puntos de Interés: {len(pois)} puestos de auxilio y tarimas oficiales")
        except Exception as e:
            logger.warning(f"Error consultando POIs en BD: {e}")

        # 5. Reportes Ciudadanos y Zonas de Congestión en BD
        try:
            recent_reports = (
                db.query(Report)
                .filter(Report.status.in_(["Pendiente", "En_Revision", "Atendido"]))
                .order_by(Report.created_at.desc())
                .limit(6)
                .all()
            )
            if recent_reports:
                report_entries = []
                for rep in recent_reports:
                    dist_str = ""
                    if has_location:
                        dist = _haversine_distance_km(user_lat, user_lon, rep.latitude, rep.longitude)
                        dist_str = f" (a {_format_distance(dist)})"
                    report_entries.append(
                        f"- [{rep.category} | Riesgo: {rep.ai_risk_level}] \"{rep.title}\"{dist_str}: {rep.description or ''}"
                    )
                context_sections.append("INCIDENCIAS Y REPORTES CIUDADANOS EN LA SENDA:\n" + "\n".join(report_entries))
                sources_used.append(f"Monitoreo Ciudadano: {len(recent_reports)} reportes en vivo")

            zone_risks = db.query(ZoneRisk).all()
            if zone_risks:
                zone_entries = [
                    f"- {zr.zone_name}: Riesgo {zr.risk_level} | Congestión {zr.congestion_percentage}%"
                    for zr in zone_risks
                ]
                context_sections.append("ESTADO DE ZONAS Y AGLOMERACIÓN:\n" + "\n".join(zone_entries))
        except Exception as e:
            logger.warning(f"Error consultando reportes/zonas en BD: {e}")

    full_context = "\n\n".join(context_sections)
    return full_context, sources_used


# ==============================================================================
# 7. GENERADOR HEURÍSTICO DE RESPALDO (FALLBACK ESTRUCTURADO)
# ==============================================================================
def _generate_smart_fallback(
    message: str,
    user_lat: Optional[float],
    user_lon: Optional[float],
    selected_day: Optional[str],
    context_text: str,
    sources_used: List[str]
) -> ChatResponse:
    """Generador heurístico de respaldo que retorna exactamente el formato estructurado

    {"reply": "...", "action": null / ROUTE} cuando no hay conexión con Gemini.
    """
    has_location = user_lat is not None and user_lon is not None
    q = message.lower()

    # 1. Detectar si piden ruta explícita hacia algún destino conocido
    route_action = _detect_requested_route(message)
    if route_action:
        dest_name = route_action["target_name"]
        dest_coords = route_action["target_coords"]
        dist_info = ""
        if has_location:
            dist = _haversine_distance_km(user_lat, user_lon, dest_coords[0], dest_coords[1])
            dist_info = f" Te encuentras a aproximadamente {_format_distance(dist)} de distancia."
        reply = (
            f"¡Con el mayor de los gustos, paisano! Te indico la orientación hacia **{dest_name}**.{dist_info}\n\n"
            f"📍 **Destino:** {dest_name}\n"
            f"🗺️ **Coordenadas:** [{dest_coords[0]}, {dest_coords[1]}].\n\n"
            "🧭 Se ha activado la acción de navegación en tu mapa interactivo para que sigas el trayecto. ¡Que viva Pasto, Carajo!"
        )
        return ChatResponse(response=reply, reply=reply, action=route_action, sources_used=sources_used)

    # 2. Respuestas según temática dinámica:
    # A. 28 de Diciembre - Arcoíris en el Asfalto
    if "28 de dic" in q or "28 dic" in q or "arcoiris" in q or "arcoíris" in q or "colorado" in q or (("hoy" in q or "qué hay" in q) and selected_day == "28-dic"):
        d = CARNIVAL_SCHEDULE_DATA["28-dic"]
        reply = (
            f"¡Hola, paisano! 🎉 El **28 de diciembre** celebramos **{d['name']}** ({d['hours']}).\n\n"
            f"🎨 {d['description']}\n"
            f"📍 Sector El Colorado (Cra 23 entre Calles 14 y 15).\n"
            f"⛔ Cierres viales: {', '.join(d['closed_points'])}.\n\n"
            "¡Una jornada cultural de arte efímero y amor por el agua! ¡Que viva Pasto, Carajo!"
        )
        action = route_action if route_action else {"type": "SET_DAY", "day_key": "28-dic", "event_title": d["name"]}
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # B. 31 de Diciembre - Años Viejos
    if "31 de dic" in q or "31 dic" in q or "año viejo" in q or "años viejos" in q or "viudas" in q or (("hoy" in q or "qué hay" in q) and selected_day == "31-dic"):
        d = CARNIVAL_SCHEDULE_DATA["31-dic"]
        reply = (
            f"¡Paisano, el **31 de diciembre** es el tradicional **{d['name']}** ({d['hours']})! 🎭\n\n"
            f"• {d['description']}\n"
            f"• **Recorrido:** Desde {d['start']} hasta {d['end']} por toda la Carrera 27.\n"
            f"• **Cierres viales:** {', '.join(d['closed_points'])}.\n\n"
            "¡El humor, la sátira política y la creatividad de los pastusos despidiendo el año!"
        )
        action = route_action if route_action else {"type": "SET_DAY", "day_key": "31-dic", "event_title": d["name"]}
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # C. 02 de Enero - Carnavalito
    if "2 de ene" in q or "02 de ene" in q or "2 ene" in q or "02 ene" in q or "carnavalito" in q or (("hoy" in q or "qué hay" in q) and selected_day == "02-ene"):
        d = CARNIVAL_SCHEDULE_DATA["02-ene"]
        reply = (
            f"¡Qué alegría, paisano! El **02 de enero** se vive el semillero del Carnaval con el **{d['name']}** ({d['hours']}). 👧🧒\n\n"
            f"• {d['description']}\n"
            f"• **Recorrido:** {d['start']} a {d['end']} por la Cra 27.\n"
            f"• **Cierres viales:** {', '.join(d['closed_points'])}.\n\n"
            "Te recomendamos acordar un punto de encuentro fijo y cuidar con cariño a los guaguas (niños)."
        )
        action = route_action if route_action else {"type": "SET_DAY", "day_key": "02-ene", "event_title": d["name"]}
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # D. 03 de Enero - Canto a la Tierra
    if "3 de ene" in q or "03 de ene" in q or "3 ene" in q or "03 ene" in q or "canto a la tierra" in q or "colectivos" in q or (("hoy" in q or "qué hay" in q) and selected_day == "03-ene"):
        d = CARNIVAL_SCHEDULE_DATA["03-ene"]
        reply = (
            f"¡Paisano! El **03 de enero** resuena la fuerza andina con el desfile **{d['name']}** ({d['hours']}). 🎶🥁\n\n"
            f"• {d['description']}\n"
            f"• **Recorrido:** Por la Carrera 27 hasta Champagnat.\n"
            f"• **Cierres viales:** {', '.join(d['closed_points'])}.\n\n"
            "¡Miles de zampoñas y bombos honrando a la Madre Tierra! ¡Que viva Nariño!"
        )
        action = route_action if route_action else {"type": "SET_DAY", "day_key": "03-ene", "event_title": d["name"]}
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # E. 04 de Enero - Familia Castañeda
    if "4 de ene" in q or "04 de ene" in q or "4 ene" in q or "04 ene" in q or "castañeda" in q or (("hoy" in q or "qué hay" in q) and selected_day == "04-ene"):
        d = CARNIVAL_SCHEDULE_DATA["04-ene"]
        reply = (
            f"¡A la orden, paisano! El **04 de enero** vivimos la **{d['name']}** ({d['hours']}). 🤠🎉\n\n"
            f"• {d['description']}\n"
            f"• **Recorrido:** Normal Superior hacia Sector Champagnat por la Carrera 27.\n"
            f"• **Cierres Viales:** {', '.join(d['closed_points'])}.\n"
            f"⚠️ **Aviso:** ¡El centro histórico y la Plaza de Nariño quedan 100% peatonalizados!"
        )
        action = route_action if route_action else {"type": "SET_DAY", "day_key": "04-ene", "event_title": d["name"]}
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # F. 05 de Enero - Día de Negros
    if "5 de ene" in q or "05 de ene" in q or "5 ene" in q or "05 ene" in q or "negros" in q or "pintica" in q or (("hoy" in q or "qué hay" in q) and selected_day == "05-ene"):
        d = CARNIVAL_SCHEDULE_DATA["05-ene"]
        reply = (
            f"¡Una pintica por la paz, paisano! El **05 de enero** es el **{d['name']}** ({d['hours']}). 🖤✨\n\n"
            f"• {d['description']}\n"
            f"• **Tarimas principales:** Plaza del Carnaval y Plaza de Nariño con orquestas en vivo.\n"
            f"• **Nota importante:** En este día no hay desfile de carrozas; las plazas son puntos de juego y encuentro.\n"
            f"• **Zonas peatonales:** {', '.join(d['closed_points'])}."
        )
        action = route_action if route_action else {"type": "SET_DAY", "day_key": "05-ene", "event_title": d["name"]}
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # G. 06 de Enero - Día de Blancos / Desfile Magno
    if "6 de ene" in q or "06 de ene" in q or "6 ene" in q or "06 ene" in q or "blancos" in q or "desfile magno" in q or "carrozas" in q or (("hoy" in q or "qué hay" in q) and selected_day == "06-ene"):
        d = CARNIVAL_SCHEDULE_DATA["06-ene"]
        reply = (
            f"¡La cumbre del Carnaval, paisano! El **06 de enero** es el majestuoso **{d['name']}** ({d['hours']}). 🎭👑\n\n"
            f"• {d['description']}\n"
            f"• **Ruta:** {d['start']} hasta {d['end']} (~7 km de recorrido).\n"
            f"• **Cierres viales:** {', '.join(d['closed_points'])}.\n\n"
            "¡Usa gafas de protección para el talco y la carioca, y disfruta de las monumentales obras de nuestros artesanos!"
        )
        action = route_action if route_action else {"type": "SET_DAY", "day_key": "06-ene", "event_title": d["name"]}
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # H. 07 de Enero - Festival del Cuy
    if "7 de ene" in q or "07 de ene" in q or "7 ene" in q or "07 ene" in q or "obonuco" in q or "catambuco" in q or (("hoy" in q or "qué hay" in q) and selected_day == "07-ene"):
        d = CARNIVAL_SCHEDULE_DATA["07-ene"]
        reply = (
            f"¡El delicioso remate del Carnaval, paisano! El **07 de enero** celebramos el **{d['name']}** ({d['hours']}). 🍽️🎶\n\n"
            f"• {d['description']}\n"
            f"• **Lugares:** Corregimientos de Obonuco y Catambuco.\n"
            f"• **Vías urbanas:** {', '.join(d['closed_points'])}. La ciudad se despeja y la fiesta se traslada al campo.\n\n"
            "¡El mejor cuy asado en vara con papas pastusas y ají de maní te espera!"
        )
        action = route_action if route_action else {"type": "SET_DAY", "day_key": "07-ene", "event_title": d["name"]}
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # I. Consulta sobre Comida, Restaurantes o Cuy
    if any(k in q for k in ["comida", "restaurante", "cuy", "empanada", "almorzar", "cenar", "comer", "hambre", "café", "cafe"]):
        rest_lines = []
        for r in PASTO_RESTAURANTS_DATA:
            is_open = is_restaurant_open_now(r["hours"])
            st = "🟢 Abierto Ahora" if is_open else "🔴 Cerrado"
            dist_str = ""
            if has_location:
                d = _haversine_distance_km(user_lat, user_lon, r["latitude"], r["longitude"])
                dist_str = f" *(a {_format_distance(d)})*"
            rest_lines.append(f"• **{r['name']}** ({r['sector']}){dist_str} — {st}\n  *Especialidad:* {r['specialty']} ({r['hours']}) [Coords: {r['latitude']}, {r['longitude']}]")

        reply = (
            "¡A la orden, paisano! En San Juan de Pasto la gastronomía es un orgullo. 🍽️✨\n\n"
            "Te recomiendo los 4 restaurantes más tradicionales de la ciudad:\n"
            "1. **Cuyquer** en Mijitayo [1.2160, -77.2915]: Cuy asado tradicional.\n"
            "2. **El Rincón del Cuy** en Av. Mijitayo / Panamericana [1.2140, -77.2870]: Cuy asado al carbón en vara.\n"
            "3. **Café San Sebastián** en Centro [1.2142, -77.2795]: Café especial nariñense de origen.\n"
            "4. **La Cabaña Andina** en Plaza Nariño [1.2145, -77.2780]: Crujientes empanadas de añejo con pipián.\n\n"
            "Detalle de estado actual:\n" + "\n".join(rest_lines) +
            "\n\nSi deseas indicaciones de cómo llegar a alguno, ¡solo pídemelo y te trazo la ruta!"
        )
        return ChatResponse(response=reply, reply=reply, action=route_action, sources_used=sources_used)

    # J. Respuesta General Dinámica
    active_day_note = ""
    if selected_day and selected_day in CARNIVAL_SCHEDULE_DATA:
        d = CARNIVAL_SCHEDULE_DATA[selected_day]
        active_day_note = f"\n\n📅 **Actualmente tienes seleccionado en el mapa:** {selected_day} - {d['name']} ({d['hours']})."

    reply = (
        "¡Hola, paisano! Te saluda tu Asistente Virtual Oficial del Carnaval de Negros y Blancos de San Juan de Pasto. 🎉\n\n"
        "Estoy listo para orientarte con información fidedigna sobre:\n"
        "1. **Programación Cultural:** 28 Dic (Arcoíris en el Asfalto), 31 Dic (Años Viejos), 02 Ene (Carnavalito), "
        "03 Ene (Canto a la Tierra), 04 Ene (Familia Castañeda), 05 Ene (Día de Negros), 06 Ene (Desfile Magno) y 07 Ene (Festival del Cuy).\n"
        "2. **Restaurantes Conocidos:** Cuyquer (Mijitayo), El Rincón del Cuy, Café San Sebastián (Centro) y La Cabaña Andina (Plaza Nariño).\n"
        "3. **Rutas y Cierres Viales:** Te indico cómo llegar a sitios de interés y qué vías se encuentran cerradas o peatonalizadas.\n"
        "4. **Puestos de Salud y Seguridad:** Ubicación de PMUs y CAIs de policía."
        f"{active_day_note}\n\n"
        "¿En qué te puedo colaborar en este momento? ¡Que viva Pasto, Carajo!"
    )
    return ChatResponse(response=reply, reply=reply, action=route_action, sources_used=sources_used)


# ==============================================================================
# 8. FUNCIÓN PRINCIPAL DE ENTRADA: generate_chat_response
# ==============================================================================
def generate_chat_response(
    message: str,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None,
    selected_day: Optional[str] = None,
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    db: Optional[Session] = None
) -> ChatResponse:
    """Procesa el mensaje del usuario utilizando Google Gemini (gemini-2.5-flash)

    con System Prompt dinámico, base de datos cultural del Carnaval y formato estructurado JSON.
    """
    effective_lat = user_lat if user_lat is not None else user_latitude
    effective_lon = user_lng if user_lng is not None else user_longitude

    # 1. Construir contexto enriquecido RAG (sin forzar días estáticos)
    full_context, sources_used = build_full_rag_context(
        db=db,
        user_lat=effective_lat,
        user_lon=effective_lon,
        selected_day=selected_day
    )

    # 2. Si no hay clave de API válida, operar con el generador heurístico estructurado
    if (
        not settings.GEMINI_API_KEY
        or settings.GEMINI_API_KEY.strip() == ""
        or settings.GEMINI_API_KEY == "tu_clave_de_gemini_aqui"
    ):
        logger.info("Operando Asistente Virtual con generador heurístico estructurado.")
        return _generate_smart_fallback(
            message=message,
            user_lat=effective_lat,
            user_lon=effective_lon,
            selected_day=selected_day,
            context_text=full_context,
            sources_used=sources_used
        )

    # 3. Invocar a Google Gemini 2.5 Flash con salida JSON estructurada
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        location_info = (
            f"Coordenadas GPS del usuario: Latitud {effective_lat}, Longitud {effective_lon}."
            if effective_lat is not None and effective_lon is not None
            else "El usuario no ha suministrado coordenadas GPS en esta consulta."
        )

        user_prompt = f"""CONTEXTO EN TIEMPO REAL Y BASE DE CONOCIMIENTO (San Juan de Pasto):
{full_context}

INFORMACIÓN GEOGRÁFICA DEL USUARIO:
{location_info}
DÍA SELECCIONADO EN EL MAPA: {selected_day or 'Ninguno fijado (responder dinámicamente según la consulta)'}

CONSULTA DEL CIUDADANO/TURISTA:
"{message}"
"""

        dynamic_system_prompt = build_dynamic_system_prompt(selected_day)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=dynamic_system_prompt,
                response_mime_type="application/json",
                response_schema=StructuredChatResponse,
                temperature=0.35,
            )
        )

        if not response or not response.text:
            return _generate_smart_fallback(
                message=message,
                user_lat=effective_lat,
                user_lon=effective_lon,
                selected_day=selected_day,
                context_text=full_context,
                sources_used=sources_used
            )

        # Parsear respuesta JSON estructurada generada por Gemini
        try:
            parsed = _clean_and_parse_json(response.text)
            reply = parsed.get("reply") or response.text.strip()
            action = parsed.get("action")
            if action and not isinstance(action, dict):
                action = None
            if not action:
                action = _detect_requested_route(message) or _detect_requested_day(message)
        except Exception as parse_err:
            logger.warning(f"Error parseando JSON de Gemini ({parse_err}). Contenido: {response.text}")
            reply = response.text.strip()
            # En caso de fallo de parseo, verificar si el usuario pedía ruta conocida o día del carnaval
            action = _detect_requested_route(message) or _detect_requested_day(message)

        return ChatResponse(
            response=reply,
            reply=reply,
            action=action,
            sources_used=sources_used
        )

    except Exception as e:
        logger.error(f"Error al conectar con Gemini: {e}")
        return _generate_smart_fallback(
            message=message,
            user_lat=effective_lat,
            user_lon=effective_lon,
            selected_day=selected_day,
            context_text=full_context,
            sources_used=sources_used
        )
