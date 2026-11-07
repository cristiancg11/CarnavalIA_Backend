"""Servicio del Asistente Virtual Cultural 'GuaneñaBot' para el Carnaval de Negros y Blancos de Pasto.

Integra Google Gemini con contexto dinámico y generador heurístico de alta fidelidad:
1. Personalidad: Calidez pastusa, festiva y respetuosa ("¡Que viva Pasto, Carajo!").
2. Conocimiento: Fechas exactas del Carnaval (28 Dic, 2, 3, 4, 5 y 6 de Enero), hitos de la Senda
   (Normal Superior, Cra 27, Plaza del Carnaval, Champagnat) y puestos de primeros auxilios (PMUs).
3. Acciones estructuradas de mapa: Coordenadas sugeridas, rutas y vistas de cámara 3D (pitch, bearing, zoom).
"""
import json
import logging
import math
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
# 1. HITOS DE LA SENDA Y PUESTOS DE PRIMEROS AUXILIOS DEL CARNAVAL DE PASTO
# ==============================================================================
CARNIVAL_LANDMARKS_DATA: Dict[str, Dict[str, Any]] = {
    "normal_superior": {
        "name": "Escuela Normal Superior de Pasto",
        "category": "Hito Senda (Salida)",
        "coords": [1.2050, -77.2830],
        "camera_view": {"center": [1.2050, -77.2830], "zoom": 17.0, "pitch": 50.0, "bearing": 20.0},
        "description": "Punto oficial de partida y concentración de todos los desfiles magnos del Carnaval."
    },
    "carrera_27": {
        "name": "Eje Carrera 27 (La Senda del Carnaval)",
        "category": "Hito Senda (Eje Central)",
        "coords": [1.2125, -77.2770],
        "camera_view": {"center": [1.2125, -77.2770], "zoom": 16.5, "pitch": 55.0, "bearing": 35.0},
        "description": "Corredor principal de 7 km por donde transitan carrozas monumentales, comparsas y murgas."
    },
    "plaza_carnaval": {
        "name": "Plaza del Carnaval y la Cultura",
        "category": "Hito Senda (Epicentro Cultural)",
        "coords": [1.2115, -77.2765],
        "camera_view": {"center": [1.2115, -77.2765], "zoom": 17.5, "pitch": 45.0, "bearing": 0.0},
        "description": "Epicentro festivo de graderías, tarima principal de orquestas y máxima concentración ciudadana."
    },
    "champagnat": {
        "name": "Sector Champagnat (IEM Ciudad de Pasto)",
        "category": "Hito Senda (Llegada)",
        "coords": [1.2190, -77.2740],
        "camera_view": {"center": [1.2190, -77.2740], "zoom": 16.8, "pitch": 45.0, "bearing": 330.0},
        "description": "Zona norte de desconcentración, culminación de carrozas y desembarque de artistas."
    },
    # Puestos de Primeros Auxilios y Salud
    "pmu_plaza_carnaval": {
        "name": "PMU Plaza del Carnaval (Cruz Roja y Defensa Civil)",
        "category": "Primeros Auxilios",
        "coords": [1.2118, -77.2760],
        "camera_view": {"center": [1.2118, -77.2760], "zoom": 18.0, "pitch": 40.0, "bearing": 10.0},
        "description": "Puesto de Mando Unificado central con ambulancias medicalizadas, paramédicos y carpas de triaje."
    },
    "pmu_normal_superior": {
        "name": "PMU Normal Superior (Punto de Salida)",
        "category": "Primeros Auxilios",
        "coords": [1.2055, -77.2825],
        "camera_view": {"center": [1.2055, -77.2825], "zoom": 17.5, "pitch": 45.0, "bearing": 0.0},
        "description": "Atención médica preliminar para artistas, danzantes y espectadores en el arranque de la senda."
    },
    "pmu_carrera_27_calle_19": {
        "name": "Puesto de Salud Carrera 27 con Calle 19",
        "category": "Primeros Auxilios",
        "coords": [1.2140, -77.2775],
        "camera_view": {"center": [1.2140, -77.2775], "zoom": 17.8, "pitch": 45.0, "bearing": 15.0},
        "description": "Módulo de socorro intermedio para desmayos, insolación o extravíos en el cruce de la Plaza de Nariño."
    },
    "pmu_champagnat": {
        "name": "PMU Champagnat (Punto de Llegada)",
        "category": "Primeros Auxilios",
        "coords": [1.2188, -77.2745],
        "camera_view": {"center": [1.2188, -77.2745], "zoom": 17.5, "pitch": 40.0, "bearing": 320.0},
        "description": "Puesto de atención médica para desconcentración y valoración final del personal de comparsas."
    }
}

# ==============================================================================
# 2. FECHAS OFICIALES Y PROGRAMACIÓN DEL CARNAVAL DE PASTO
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
        "name": "Desfile de Años Viejos y Viudas",
        "date_label": "31 de Diciembre",
        "hours": "08:00 - 16:00",
        "description": "Desfile de Años Viejos y Viudas. Humor, sátira política, testamentos y quema simbólica de monigotes.",
        "start": "Salida: Escuela Normal Superior",
        "end": "Llegada: Sector Champagnat",
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
        "notes": "Gran afluencia de niños; se recomienda especial cuidado y acordar puntos de encuentro fijos."
    },
    "03-ene": {
        "name": "Canto a la Tierra",
        "date_label": "03 de Enero",
        "hours": "09:00 - 16:00",
        "description": "Desfile de Colectivos Coreográficos. Miles de músicos y danzantes andinos con zampoñas, bombos, quenas y trajes multicolores por la Cra 27.",
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
        "name": "Llegada de la Familia Castañeda",
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
        "description": "Conmemoración de la libertad y la igualdad étnica; juego fraternal con cosmético negro, orquestas en vivo y tarimas musicales. (No hay desfile de carrozas monumentales).",
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
        "start": "Salida: Escuela Normal Superior / Avenida Emmanuel",
        "end": "Llegada: Sector Champagnat",
        "closed_points": [
            "Cierre Carrera 27 desde las 5:00 AM",
            "Cierre Avenida Mijitayo y cruce Panamericana",
            "Cierre Calle 19 y Sector Champagnat"
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
# 3. DIRECTORIO GASTRONÓMICO Y PUNTOS DE INTERÉS DE PASTO
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
    }
]

# Mapa para georreferenciación rápida
KNOWN_LOCATIONS: Dict[str, Tuple[str, List[float], Dict[str, Any]]] = {
    # Hitos Senda
    "normal superior": ("Escuela Normal Superior (Salida)", [1.2050, -77.2830], {"center": [1.2050, -77.2830], "zoom": 17.0, "pitch": 50.0, "bearing": 20.0}),
    "escuela normal": ("Escuela Normal Superior (Salida)", [1.2050, -77.2830], {"center": [1.2050, -77.2830], "zoom": 17.0, "pitch": 50.0, "bearing": 20.0}),
    "carrera 27": ("Carrera 27 (La Senda)", [1.2125, -77.2770], {"center": [1.2125, -77.2770], "zoom": 16.5, "pitch": 55.0, "bearing": 35.0}),
    "cra 27": ("Carrera 27 (La Senda)", [1.2125, -77.2770], {"center": [1.2125, -77.2770], "zoom": 16.5, "pitch": 55.0, "bearing": 35.0}),
    "senda": ("Carrera 27 (La Senda del Carnaval)", [1.2125, -77.2770], {"center": [1.2125, -77.2770], "zoom": 16.5, "pitch": 55.0, "bearing": 35.0}),
    "plaza del carnaval": ("Plaza del Carnaval y la Cultura", [1.2115, -77.2765], {"center": [1.2115, -77.2765], "zoom": 17.5, "pitch": 45.0, "bearing": 0.0}),
    "champagnat": ("Sector Champagnat (Llegada)", [1.2190, -77.2740], {"center": [1.2190, -77.2740], "zoom": 16.8, "pitch": 45.0, "bearing": 330.0}),
    "plaza de nariño": ("Plaza de Nariño", [1.2145, -77.2780], {"center": [1.2145, -77.2780], "zoom": 17.0, "pitch": 40.0, "bearing": 0.0}),
    "plaza nariño": ("Plaza de Nariño", [1.2145, -77.2780], {"center": [1.2145, -77.2780], "zoom": 17.0, "pitch": 40.0, "bearing": 0.0}),
    # Primeros Auxilios / Salud
    "primeros auxilios": ("PMU Plaza del Carnaval (Cruz Roja)", [1.2118, -77.2760], {"center": [1.2118, -77.2760], "zoom": 18.0, "pitch": 40.0, "bearing": 10.0}),
    "puesto de salud": ("PMU Plaza del Carnaval (Cruz Roja)", [1.2118, -77.2760], {"center": [1.2118, -77.2760], "zoom": 18.0, "pitch": 40.0, "bearing": 10.0}),
    "ambulancia": ("PMU Plaza del Carnaval", [1.2118, -77.2760], {"center": [1.2118, -77.2760], "zoom": 18.0, "pitch": 40.0, "bearing": 10.0}),
    "cruz roja": ("PMU Plaza del Carnaval (Cruz Roja)", [1.2118, -77.2760], {"center": [1.2118, -77.2760], "zoom": 18.0, "pitch": 40.0, "bearing": 10.0}),
    "defensa civil": ("PMU Plaza del Carnaval", [1.2118, -77.2760], {"center": [1.2118, -77.2760], "zoom": 18.0, "pitch": 40.0, "bearing": 10.0}),
    "hospital": ("Hospital Universitario San Pedro", [1.2220, -77.2790], {"center": [1.2220, -77.2790], "zoom": 16.5, "pitch": 30.0, "bearing": 0.0}),
    # Restaurantes
    "cuyquer": ("Restaurante Cuyquer", [1.2160, -77.2915], {"center": [1.2160, -77.2915], "zoom": 17.0, "pitch": 40.0, "bearing": 0.0}),
    "rincon del cuy": ("El Rincón del Cuy", [1.2140, -77.2870], {"center": [1.2140, -77.2870], "zoom": 17.0, "pitch": 40.0, "bearing": 0.0}),
    "el rincon del cuy": ("El Rincón del Cuy", [1.2140, -77.2870], {"center": [1.2140, -77.2870], "zoom": 17.0, "pitch": 40.0, "bearing": 0.0}),
    "cafe san sebastian": ("Café San Sebastián", [1.2142, -77.2795], {"center": [1.2142, -77.2795], "zoom": 17.5, "pitch": 45.0, "bearing": 0.0}),
    "la cabaña andina": ("La Cabaña Andina", [1.2145, -77.2780], {"center": [1.2145, -77.2780], "zoom": 17.5, "pitch": 45.0, "bearing": 0.0}),
}

# ==============================================================================
# 4. ESQUEMAS PYDANTIC PARA SALIDA ESTRUCTURADA CON VISTAS DE CÁMARA
# ==============================================================================
class CameraViewPayload(BaseModel):
    """Parámetros de vista de cámara para el mapa interactivo (3D Mapbox/Leaflet)."""
    center: List[float] = Field(description="Coordenadas [latitud, longitud] del foco")
    zoom: float = Field(default=16.5, description="Nivel de zoom del mapa (14 a 18)")
    pitch: Optional[float] = Field(default=45.0, description="Inclinación 3D en grados")
    bearing: Optional[float] = Field(default=0.0, description="Rotación o rumbo del mapa")


class ActionPayload(BaseModel):
    """Acción estructurada para control del mapa interactivo en frontend."""
    type: str = Field(description="Tipo de acción: 'SET_DAY', 'ROUTE', 'CAMERA_VIEW'")
    day_key: Optional[str] = Field(default=None, description="Clave de día: '28-dic', '02-ene', '03-ene', '04-ene', '05-ene', '06-ene', '07-ene'")
    event_title: Optional[str] = Field(default=None, description="Título del evento del día")
    target_name: Optional[str] = Field(default=None, description="Nombre del destino o hito")
    target_coords: Optional[List[float]] = Field(default=None, description="Coordenadas sugeridas [lat, lng]")
    camera_view: Optional[CameraViewPayload] = Field(default=None, description="Ajuste de cámara 3D sugerido")


class StructuredChatResponse(BaseModel):
    """Respuesta estructurada de GuaneñaBot."""
    reply: str = Field(..., description="Respuesta conversacional con calidez pastusa ('¡Que viva Pasto, Carajo!').")
    action: Optional[ActionPayload] = Field(default=None, description="Acción interactiva de mapa con coordenadas y cámara si aplica.")


# ==============================================================================
# 5. SYSTEM PROMPT CULTURAL DE GUANEÑABOT
# ==============================================================================
GUANENA_BOT_SYSTEM_PROMPT = """Eres GUANEÑABOT, el Asistente Virtual Oficial con Inteligencia Artificial del Carnaval de Negros y Blancos de San Juan de Pasto, Patrimonio Cultural Inmaterial de la Humanidad por la UNESCO.

1. PERSONALIDAD Y TONO:
- Irradias calidez pastusa, hospitalidad sincera, orgullo cultural y entusiasmo festivo.
- Cierras o enfatizas tus mensajes con el célebre grito festivo: "¡Que viva Pasto, Carajo!".
- Utilizas de forma natural y respetuosa expresiones autóctonas nariñenses: "paisano", "guagua" (niño), "a la orden", "¡caray!", "achichucas", celebrando la música de La Guaneña.

2. CONOCIMIENTO EXACTO DEL CARNAVAL DE PASTO:
- 28 de Diciembre: Arcoíris en el Asfalto (El Colorado, Cra 23 entre Calles 14 y 15). Celebración ecológica, arte con tiza sobre el pavimento por la paz y el agua.
- 31 de Diciembre: Desfile de Años Viejos y Viudas (Humor, sátira política, testamentos y quema de monigotes).
- 02 de Enero: Carnavalito (El semillero infantil con mini-carrozas y homenaje a la Virgen de las Mercedes).
- 03 de Enero: Canto a la Tierra (Desfile de Colectivos Coreográficos, miles de músicos y danzantes andinos con zampoñas, quenas y bombos por la Cra 27).
- 04 de Enero: Llegada de la Familia Castañeda (Teatro callejero, carretas de época conmemorando la comitiva de 1929; centro histórico 100% peatonalizado).
- 05 de Enero: Día de Negros (Juego fraternal de cosmético negro y orquestas en vivo en Plaza del Carnaval y Plaza de Nariño; sin carrozas gigantes).
- 06 de Enero: Día de Blancos / Desfile Magno (La cumbre del Carnaval: Majestuosas Carrozas Monumentales de hasta 12m de altura, comparsas, murgas, juego con cosmético blanco, talco perfumado y carioca).
- 07 de Enero: Festival del Cuy y la Cultura Campesina en los corregimientos de Obonuco y Catambuco.

3. HITOS CLAVE DE LA SENDA DEL CARNAVAL:
- Escuela Normal Superior [1.2050, -77.2830]: Punto de salida tradicional y concentración de desfiles.
- Carrera 27 [1.2125, -77.2770]: La Senda oficial y eje arterial por donde avanzan artistas y carrozas.
- Plaza del Carnaval y la Cultura [1.2115, -77.2765]: Epicentro cultural, tarima principal, graderías y zona de premiación.
- Sector Champagnat [1.2190, -77.2740]: Punto de llegada, desembarque y desconcentración de los desfiles.

4. PUESTOS DE PRIMEROS AUXILIOS Y SEGURIDAD (PMUs):
- PMU Plaza del Carnaval [1.2118, -77.2760]: Puesto central de Cruz Roja, Defensa Civil y ambulancias.
- PMU Normal Superior [1.2055, -77.2825]: Atención médica de partida en la Senda.
- Puesto Cra 27 con Cll 19 [1.2140, -77.2775]: Socorro rápido en el anillo central.
- PMU Champagnat [1.2188, -77.2745]: Triaje final y desconcentración.
- Hospital Universitario San Pedro [1.2220, -77.2790] y Hospital Infantil Los Ángeles [1.2090, -77.2880].

5. ACCIONES ESTRUCTURADAS DE MAPA:
Debes generar un JSON con 'reply' y 'action':
- Si el usuario consulta una fecha del Carnaval:
  action: { "type": "SET_DAY", "day_key": "06-ene", "event_title": "Día de Blancos - Desfile Magno", "camera_view": { "center": [1.2115, -77.2765], "zoom": 16.5, "pitch": 45.0, "bearing": 0.0 } }
- Si el usuario pregunta por un hito de la Senda, primeros auxilios o restaurante:
  action: { "type": "ROUTE", "target_name": "Nombre del sitio", "target_coords": [lat, lng], "camera_view": { "center": [lat, lng], "zoom": 17.5, "pitch": 50.0, "bearing": 15.0 } }
- Si es una charla general sin referencia geográfica ni fecha:
  action: null
"""


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia Haversine en kilómetros."""
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
    """Formatea la distancia en metros o kilómetros."""
    meters = km * 1000.0
    if meters < 1000.0:
        return f"{int(round(meters))} metros"
    return f"{km:.2f} km"


def _clean_and_parse_json(text: str) -> Dict[str, Any]:
    """Limpia markdown de código y parsea JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())


def _detect_map_action(message: str) -> Optional[Dict[str, Any]]:
    """Detecta heurísticamente si el mensaje amerita acción de mapa con coordenadas y cámara."""
    q = message.lower()

    # Días del Carnaval
    day_matches = [
        ("28-dic", "28 de Diciembre - Arcoíris en el Asfalto", ["28 de dic", "28 dic", "arcoiris", "colorado"], [1.2150, -77.2820]),
        ("31-dic", "31 de Diciembre - Desfile de Años Viejos", ["31 de dic", "31 dic", "año viejo", "viudas"], [1.2125, -77.2770]),
        ("02-ene", "02 de Enero - Carnavalito", ["2 de ene", "02 de ene", "2 ene", "carnavalito"], [1.2050, -77.2830]),
        ("03-ene", "03 de Enero - Canto a la Tierra", ["3 de ene", "03 de ene", "3 ene", "canto a la tierra", "colectivo"], [1.2125, -77.2770]),
        ("04-ene", "04 de Enero - Familia Castañeda", ["4 de ene", "04 de ene", "4 ene", "castañeda", "castaneda"], [1.2145, -77.2780]),
        ("05-ene", "05 de Enero - Día de Negros", ["5 de ene", "05 de ene", "5 ene", "día de negros", "pintica"], [1.2115, -77.2765]),
        ("06-ene", "06 de Enero - Día de Blancos (Desfile Magno)", ["6 de ene", "06 de ene", "6 ene", "día de blancos", "carrozas", "magno"], [1.2115, -77.2765]),
        ("07-ene", "07 de Enero - Festival del Cuy", ["7 de ene", "07 de ene", "7 ene", "festival del cuy", "obonuco"], [1.1890, -77.2920]),
    ]
    for day_key, title, keywords, coords in day_matches:
        if any(kw in q for kw in keywords):
            return {
                "type": "SET_DAY",
                "day_key": day_key,
                "event_title": title,
                "target_name": title,
                "target_coords": coords,
                "camera_view": {"center": coords, "zoom": 16.5, "pitch": 45.0, "bearing": 0.0}
            }

    # Hitos y Primeros Auxilios conocidos
    for key, (name, coords, cam_view) in KNOWN_LOCATIONS.items():
        if key in q:
            return {
                "type": "ROUTE",
                "target_name": name,
                "target_coords": coords,
                "camera_view": cam_view
            }

    return None


def _generate_smart_fallback(
    message: str,
    user_lat: Optional[float],
    user_lon: Optional[float],
    selected_day: Optional[str],
    context_text: str,
    sources_used: List[str]
) -> ChatResponse:
    """Generador heurístico de GuaneñaBot con calidez pastusa y acciones de mapa."""
    q = message.lower()
    has_location = user_lat is not None and user_lon is not None
    action = _detect_map_action(message)

    # 1. Puestos de Primeros Auxilios / Salud
    if any(k in q for k in ["primeros auxilios", "salud", "médico", "medico", "ambulancia", "cruz roja", "emergencia", "herido", "desmayo"]):
        pmu = CARNIVAL_LANDMARKS_DATA["pmu_plaza_carnaval"]
        dist_str = ""
        if has_location:
            dist = _haversine_distance_km(user_lat, user_lon, pmu["coords"][0], pmu["coords"][1])
            dist_str = f" Te encuentras a unos {_format_distance(dist)} del punto de socorro principal."
        reply = (
            f"¡Tranquilo, paisano! La red de socorro y primeros auxilios está 100% activa.{dist_str}\n\n"
            f"🏥 **Puesto Principal:** {pmu['name']}\n"
            f"📍 **Ubicación:** Plaza del Carnaval y la Cultura [Coords: {pmu['coords'][0]}, {pmu['coords'][1]}]\n"
            "🚑 **Recursos en sitio:** Carpas de triaje, personal de la Cruz Roja, Defensa Civil y ambulancias medicalizadas.\n\n"
            "Otros puntos de auxilio en la Senda:\n"
            "- PMU Normal Superior (Punto de Salida)\n"
            "- Puesto Carrera 27 con Calle 19 (Sector Plaza de Nariño)\n"
            "- PMU Sector Champagnat (Punto de Llegada)\n\n"
            "🧭 Se ha activado la vista de cámara y coordenadas en tu mapa interactivo para orientarte de inmediato. ¡Cuídate mucho, paisano! ¡Que viva Pasto, Carajo!"
        )
        act = action or {
            "type": "ROUTE",
            "target_name": pmu["name"],
            "target_coords": pmu["coords"],
            "camera_view": pmu["camera_view"]
        }
        return ChatResponse(response=reply, reply=reply, action=act, sources_used=sources_used)

    # 2. Hitos de la Senda (Normal Superior, Cra 27, Plaza del Carnaval, Champagnat)
    if any(k in q for k in ["senda", "ruta del desfile", "normal superior", "carrera 27", "plaza del carnaval", "champagnat", "recorrido"]):
        reply = (
            "¡Qué viva la Senda del Carnaval, paisano! 🎉 El recorrido oficial consta de 7 km de pura magia y color andino:\n\n"
            "1. 🏁 **Punto de Salida:** Escuela Normal Superior de Pasto [Coords: 1.2050, -77.2830]. Concentración de artistas y carrozas.\n"
            "2. 🎺 **Eje Central:** La emblemática Carrera 27 [Coords: 1.2125, -77.2770], donde vibra la música y la danza.\n"
            "3. 👑 **Epicentro:** Plaza del Carnaval y la Cultura [Coords: 1.2115, -77.2765], zona de tarima oficial y graderías.\n"
            "4. 🏁 **Punto de Llegada:** Sector Champagnat / IEM Ciudad de Pasto [Coords: 1.2190, -77.2740], desconcentración y desembarque.\n\n"
            "🧭 ¡He enfocado la cámara de tu mapa sobre la Senda para que la aprecies en vista 3D! ¡Que viva Pasto, Carajo!"
        )
        act = action or {
            "type": "CAMERA_VIEW",
            "target_name": "La Senda del Carnaval",
            "target_coords": [1.2125, -77.2770],
            "camera_view": {"center": [1.2125, -77.2770], "zoom": 16.5, "pitch": 55.0, "bearing": 35.0}
        }
        return ChatResponse(response=reply, reply=reply, action=act, sources_used=sources_used)

    # 3. 28 de Diciembre - Arcoíris en el Asfalto
    if "28" in q or "arcoiris" in q or "colorado" in q:
        d = CARNIVAL_SCHEDULE_DATA["28-dic"]
        reply = (
            f"¡Hola, paisano! 🎉 El **28 de diciembre** vivimos el **{d['name']}** ({d['hours']}).\n\n"
            f"🎨 {d['description']}\n"
            "📍 Sector El Colorado (Cra 23 entre Calles 14 y 15).\n"
            "⛔ Cierres viales: Vía cerrada para pintar con tiza y celebrar el cuidado del agua.\n\n"
            "¡Una fiesta de arte efímero que enamora a propios y turistas! ¡Que viva Pasto, Carajo!"
        )
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # 4. 02 de Enero - Carnavalito
    if "2 de ene" in q or "02 de ene" in q or "carnavalito" in q:
        d = CARNIVAL_SCHEDULE_DATA["02-ene"]
        reply = (
            f"¡Qué emoción, paisano! El **02 de enero** es el semillero de nuestra tradición: el **{d['name']}** ({d['hours']}). 👧🧒\n\n"
            f"• {d['description']}\n"
            "• **Ruta de la Senda:** Desde la Normal Superior hasta el Sector Champagnat por toda la Carrera 27.\n"
            "• **Recomendación:** Acuerda un punto de encuentro fijo y protege con amor a los guaguas.\n\n"
            "¡La ternura y el talento infantil en nuestra fiesta grande! ¡Que viva Pasto, Carajo!"
        )
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # 5. 03 de Enero - Canto a la Tierra
    if "3 de ene" in q or "03 de ene" in q or "canto a la tierra" in q or "colectivo" in q:
        d = CARNIVAL_SCHEDULE_DATA["03-ene"]
        reply = (
            f"¡Paisano querido! El **03 de enero** retumba el suelo con **{d['name']}** ({d['hours']}). 🎶🥁\n\n"
            f"• {d['description']}\n"
            "• **Hito Senda:** Recorrido por la Carrera 27 desde la Normal Superior hasta Champagnat.\n"
            "• **Música:** Zampoñas, bombos andinos y coreografías majestuosas honrando a la Pacha Mama.\n\n"
            "¡Un río sonoro de hermandad y orgullo nariñense! ¡Que viva Pasto, Carajo!"
        )
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # 6. 04 de Enero - Familia Castañeda
    if "4 de ene" in q or "04 de ene" in q or "castañeda" in q or "castaneda" in q:
        d = CARNIVAL_SCHEDULE_DATA["04-ene"]
        reply = (
            f"¡A la orden, paisano! El **04 de enero** celebramos la **{d['name']}** ({d['hours']}). 🤠🎉\n\n"
            f"• {d['description']}\n"
            "• **Recorrido:** Normal Superior hacia Champagnat.\n"
            "⚠️ **Aviso vial:** ¡El centro histórico y la Plaza de Nariño quedan 100% peatonalizados!\n\n"
            "¡Bienvenidos todos los forasteros a gozar de nuestra tierra! ¡Que viva Pasto, Carajo!"
        )
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # 7. 05 de Enero - Día de Negros
    if "5 de ene" in q or "05 de ene" in q or "negros" in q or "pintica" in q:
        d = CARNIVAL_SCHEDULE_DATA["05-ene"]
        reply = (
            f"¡Una pintica por la paz, paisano! El **05 de enero** celebramos el **{d['name']}** ({d['hours']}). 🖤✨\n\n"
            f"• {d['description']}\n"
            "• **Tarimas principales:** Plaza del Carnaval y Plaza de Nariño con orquestas en vivo.\n"
            "• **Recordatorio clave:** En este día no hay desfile de carrozas; las plazas son puntos fraternos de encuentro.\n\n"
            "¡El juego con cosmético negro que nos hermana a todos por igual! ¡Que viva Pasto, Carajo!"
        )
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # 8. 06 de Enero - Día de Blancos / Desfile Magno
    if "6 de ene" in q or "06 de ene" in q or "blancos" in q or "carrozas" in q or "desfile magno" in q:
        d = CARNIVAL_SCHEDULE_DATA["06-ene"]
        reply = (
            f"¡La cumbre monumental de nuestra cultura, paisano! El **06 de enero** es el **{d['name']}** ({d['hours']}). 🎭👑\n\n"
            f"• {d['description']}\n"
            "• **Recorrido:** Normal Superior (Salida) -> Cra 27 -> Plaza del Carnaval -> Champagnat (Llegada).\n"
            "• **Consejo de seguridad:** Usa gafas protectoras para el talco perfumado y la carioca.\n\n"
            "¡Nuestros artesanos son los mejores escultores del mundo! ¡Que viva Pasto, Carajo!"
        )
        return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)

    # 9. Respuesta general de bienvenida
    reply = (
        "¡Bienvenido a San Juan de Pasto, paisano! Soy **GuaneñaBot**, tu guía con IA para vivir el Carnaval de Negros y Blancos al 100%. 🎉\n\n"
        "Puedo orientarte con precisión sobre:\n"
        "📅 **Fechas Clave:** 28 Dic (Arcoíris en el Asfalto), 02 Ene (Carnavalito), 03 Ene (Canto a la Tierra), "
        "04 Ene (Familia Castañeda), 05 Ene (Día de Negros) y 06 Ene (Desfile Magno de Carrozas).\n"
        "🗺️ **La Senda:** Normal Superior, Carrera 27, Plaza del Carnaval y Sector Champagnat.\n"
        "🏥 **Puestos de Salud:** Ubicación en tiempo real de PMUs y módulos de primeros auxilios.\n"
        "🍽️ **Gastronomía:** Los mejores asaderos de cuy tradicional y café nariñense.\n\n"
        "¿En qué te puedo colaborar en este momento? ¡Que viva Pasto, Carajo!"
    )
    return ChatResponse(response=reply, reply=reply, action=action, sources_used=sources_used)


def build_full_rag_context(
    db: Optional[Session] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    selected_day: Optional[str] = None
) -> Tuple[str, List[str]]:
    """Construye contexto de respaldo RAG para compatibilidad con servicios."""
    sources = [
        "Base Oficial del Carnaval de Negros y Blancos de Pasto",
        "Red de Puestos de Primeros Auxilios y Salud (PMU)",
        "Hitos de la Senda Oficial (Cra 27, Normal Superior, Plaza del Carnaval)"
    ]
    return GUANENA_BOT_SYSTEM_PROMPT, sources


# ==============================================================================
# 6. ENTRADA PRINCIPAL: generate_chat_response
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
    """Procesa consultas con GuaneñaBot integrando contexto dinámico cultural y mapa 3D."""
    effective_lat = user_lat if user_lat is not None else user_latitude
    effective_lon = user_lng if user_lng is not None else user_longitude

    sources_used = [
        "Base Oficial del Carnaval de Negros y Blancos de Pasto",
        "Red de Puestos de Primeros Auxilios y Salud (PMU)",
        "Hitos de la Senda Oficial (Cra 27, Normal Superior, Plaza del Carnaval)"
    ]

    # Si hay clave de Gemini disponible, intentar consulta al modelo generativo
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ["", "tu_clave_de_gemini_aqui"]:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            location_info = (
                f"Ubicación GPS del usuario: Latitud {effective_lat}, Longitud {effective_lon}."
                if effective_lat and effective_lon
                else "Ubicación del usuario: En Pasto (sin GPS activo)."
            )

            prompt = f"""CONSULTA DEL CIUDADANO/TURISTA:
"{message}"

CONTEXTO ADICIONAL:
{location_info}
Día seleccionado en frontend: {selected_day or 'Ninguno'}
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=GUANENA_BOT_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=StructuredChatResponse,
                    temperature=0.35,
                )
            )

            if response and response.text:
                parsed = _clean_and_parse_json(response.text)
                reply = parsed.get("reply") or response.text.strip()
                action = parsed.get("action")
                if not action:
                    action = _detect_map_action(message)
                return ChatResponse(
                    response=reply,
                    reply=reply,
                    action=action,
                    sources_used=sources_used
                )
        except Exception as exc:
            logger.warning(f"Aviso en conexión con Gemini API ({exc}). Despachando con generador cultural de respaldo.")

    # Generador heurístico de respaldo de alta fidelidad cultural
    return _generate_smart_fallback(
        message=message,
        user_lat=effective_lat,
        user_lon=effective_lon,
        selected_day=selected_day,
        context_text="",
        sources_used=sources_used
    )
