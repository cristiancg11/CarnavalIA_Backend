"""Official GIS landmarks, route coordinates, and strategic urban telemetry for San Juan de Pasto.

Provides verified coordinates for the official Senda del Carnaval path and nearby
critical public services (restrooms, police, emergency health, music stages, shopping,
and crowd-risk congestion zones) for Leaflet/OSRM map visualization.
"""
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Senda del Carnaval - Official Route Telemetry
# ---------------------------------------------------------------------------

SENDA_START: Dict[str, Any] = {
    "name": "Estadio Departamental Libertad",
    "coordinates": [1.2025, -77.2762],
    "description": "Punto oficial de partida y concentración de carrozas, comparsas y murgas del Carnaval.",
}

SENDA_FINISH: Dict[str, Any] = {
    "name": "Fuente de la Transparencia / Torobajo",
    "coordinates": [1.2330, -77.2845],
    "description": "Punto de culminación oficial del desfile sobre la Avenida de los Estudiantes y llegada a Torobajo.",
}

# Ordered street-by-street waypoints for Leaflet Polyline rendering
SENDA_OFFICIAL_PATH: List[List[float]] = [
    [1.2025, -77.2762],  # Estadio Departamental Libertad (Inicio)
    [1.2052, -77.2766],  # Carrera 4 hacia el norte
    [1.2095, -77.2770],  # Glorieta Lorenzo de Aldana
    [1.2115, -77.2778],  # Giro hacia Calle 19
    [1.2136, -77.2785],  # Plaza del Carnaval y la Cultura
    [1.2142, -77.2782],  # Conexión Carrera 27
    [1.2148, -77.2780],  # Plaza de Nariño
    [1.2190, -77.2800],  # Calle 18 hacia el norte
    [1.2260, -77.2825],  # Avenida de los Estudiantes
    [1.2330, -77.2845],  # Fuente de la Transparencia / Torobajo (Llegada)
]


# ---------------------------------------------------------------------------
# Strategic Urban Service Landmarks in Pasto
# ---------------------------------------------------------------------------

NEARBY_SERVICE_POINTS: List[Dict[str, Any]] = [
    # Restrooms (Baños públicos)
    {
        "name": "Batería Sanitaria Plaza del Carnaval",
        "category": "restroom",
        "coordinates": [1.2130, -77.2780],
        "description": "Batería de baños públicos y módulos sanitarios portátiles contiguos a la Plaza del Carnaval.",
    },
    {
        "name": "Módulo Sanitario Centro - Pasaje Corazón de Jesús",
        "category": "restroom",
        "coordinates": [1.2152, -77.2775],
        "description": "Servicios higiénicos públicos en zona céntrica habilitados durante fiestas decembrinas y carnavalescas.",
    },
    {
        "name": "Servicios Sanitarios Estadio Libertad",
        "category": "restroom",
        "coordinates": [1.2030, -77.2758],
        "description": "Punto sanitario zona sur en las inmediaciones del Estadio Libertad para concentración inicial.",
    },

    # Police CAIs (Seguridad y Convivencia)
    {
        "name": "CAI Plaza de Nariño",
        "category": "police",
        "coordinates": [1.2140, -77.2792],
        "description": "Puesto policial principal del centro histórico, cuadrante de vigilancia y recepción de denuncias.",
    },
    {
        "name": "CAI Lorenzo de Aldana",
        "category": "police",
        "coordinates": [1.2088, -77.2765],
        "description": "Puesto policial del sector sur vigilando la glorieta Lorenzo de Aldana y Carrera 4.",
    },
    {
        "name": "CAI Morasurco",
        "category": "police",
        "coordinates": [1.2290, -77.2830],
        "description": "Puesto de control policial sector norte sobre la Avenida de los Estudiantes hacia Torobajo.",
    },

    # Health (Salud y Primeros Auxilios / Cruz Roja / Defensa Civil)
    {
        "name": "Puesto de Socorro Cruz Roja - Plaza del Carnaval",
        "category": "health",
        "coordinates": [1.2128, -77.2779],
        "description": "Puesto de atención prehospitalaria, carpa de triage, ambulancia y paramédicos de la Cruz Roja.",
    },
    {
        "name": "Puesto de Emergencias Médicas - Calle 19 con Cra 27",
        "category": "health",
        "coordinates": [1.2195, -77.2801],
        "description": "Módulo de socorro asistencial de la Defensa Civil y brigadistas de primeros auxilios.",
    },

    # Music & Cultural Stages (Tarimas y Conciertos)
    {
        "name": "Tarima Principal Plaza del Carnaval",
        "category": "stage",
        "coordinates": [1.2136, -77.2785],
        "description": "Escenario principal de orquestas nacionales e internacionales, murgas y conciertos oficiales.",
    },
    {
        "name": "Tarima Cultural Plaza de Nariño",
        "category": "stage",
        "coordinates": [1.2148, -77.2780],
        "description": "Escenario de música andina, ensambles de vientos, danza tradicional y folclor nariñense.",
    },
    {
        "name": "Tarima Alternativa Plaza del Carrizal",
        "category": "stage",
        "coordinates": [1.2225, -77.2815],
        "description": "Escenario de son sureño, música campesina, colectivos juveniles y trovadores.",
    },

    # Shopping (Centros Comerciales y Abastecimiento)
    {
        "name": "Centro Comercial Sebastián de Belalcázar",
        "category": "shopping",
        "coordinates": [1.2160, -77.2765],
        "description": "Centro comercial céntrico con cajeros automáticos, hidratación, farmacias y gastronomía típica.",
    },
    {
        "name": "Centro Comercial Unicentro Pasto",
        "category": "shopping",
        "coordinates": [1.2285, -77.2835],
        "description": "Gran complejo comercial del norte con amplia plazoleta de comidas, bancos y zona de descanso.",
    },

    # Risk & Crowd Congestion Zones (Zonas de Aglomeración)
    {
        "name": "Embudo Carrera 27 con Plaza del Carnaval",
        "category": "risk_zone",
        "coordinates": [1.2135, -77.2788],
        "description": "Zona de altísima afluencia y cuello de botella peatonal durante el paso de carrozas gigantes. Extreme precauciones.",
    },
]


# ---------------------------------------------------------------------------
# Default Official Schedules per Carnival Day
# ---------------------------------------------------------------------------

CARNAVAL_SCHEDULES: Dict[str, Dict[str, str]] = {
    "jan_02": {
        "start_time": "09:00 AM",
        "estimated_arrival_time": "01:30 PM",
        "start_location": "Templo San Juan Bautista",
        "finish_location": "Santuario de Nuestra Señora de las Mercedes",
        "event_name": "Ofrenda a la Virgen de las Mercedes y Carnavalito",
    },
    "jan_03": {
        "start_time": "10:00 AM",
        "estimated_arrival_time": "03:00 PM",
        "start_location": "Estadio Departamental Libertad",
        "finish_location": "Plaza del Carnaval y la Cultura",
        "event_name": "Canto a la Tierra (Desfile de Colectivos Coreográficos)",
    },
    "jan_04": {
        "start_time": "10:00 AM",
        "estimated_arrival_time": "03:30 PM",
        "start_location": "Estadio Departamental Libertad",
        "finish_location": "Avenida de los Estudiantes",
        "event_name": "Llegada de la Familia Castañeda",
    },
    "jan_05": {
        "start_time": "08:00 AM",
        "estimated_arrival_time": "08:00 PM",
        "start_location": "Plaza de Nariño",
        "finish_location": "Plazas y Comunas de Pasto",
        "event_name": "Día de Negros (Juego de Cosmético e Identidad)",
    },
    "jan_06": {
        "start_time": "09:00 AM",
        "estimated_arrival_time": "04:30 PM",
        "start_location": "Estadio Departamental Libertad",
        "finish_location": "Avenida de los Estudiantes / Torobajo",
        "event_name": "Desfile Magno (Día de Blancos - Carrozas Monumentales)",
    },
    "jan_07": {
        "start_time": "10:00 AM",
        "estimated_arrival_time": "06:00 PM",
        "start_location": "Catambuco y Obonuco",
        "finish_location": "Corregimientos del Sur",
        "event_name": "Festival del Cuy y la Cultura Campesina",
    },
}


def get_schedule_for_query(text: str) -> Dict[str, str]:
    """Infer the appropriate schedule based on keywords in user prompt."""
    query_lower = text.lower()
    if any(k in query_lower for k in ["6 de enero", "magno", "blancos", "carroza"]):
        return CARNAVAL_SCHEDULES["jan_06"]
    if any(k in query_lower for k in ["5 de enero", "negros", "cosmetico", "juego"]):
        return CARNAVAL_SCHEDULES["jan_05"]
    if any(k in query_lower for k in ["4 de enero", "castañeda", "castaneda", "pericles"]):
        return CARNAVAL_SCHEDULES["jan_04"]
    if any(k in query_lower for k in ["3 de enero", "canto a la tierra", "coreografico", "danzantes"]):
        return CARNAVAL_SCHEDULES["jan_03"]
    if any(k in query_lower for k in ["2 de enero", "carnavalito", "mercedes", "ofrenda"]):
        return CARNAVAL_SCHEDULES["jan_02"]
    if any(k in query_lower for k in ["7 de enero", "cuy", "catambuco", "obonuco"]):
        return CARNAVAL_SCHEDULES["jan_07"]

    # Default to the most requested flagship event: Desfile Magno (Jan 6)
    return CARNAVAL_SCHEDULES["jan_06"]
