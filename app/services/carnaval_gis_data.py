"""Official GIS landmarks, strict Senda waypoints, and proximity locator for San Juan de Pasto.

Stores the official Senda del Carnaval sequential polyline and provides real-time
spatial proximity sorting against verified local points of interest.
"""
from typing import Any, Dict, List, Optional
from app.services.spatial_utils import calculate_distance_meters, format_proximity_label


# ---------------------------------------------------------------------------
# Senda del Carnaval - Official Route Telemetry
# ---------------------------------------------------------------------------

SENDA_START: Dict[str, Any] = {
    "name": "Estadio Departamental Libertad",
    "coordinates": [1.2025, -77.2762],
    "address": "Calle 2 con Carrera 4, Barrio San Vicente / Libertad",
    "description": "Punto oficial de partida y concentración de carrozas, comparsas y murgas del Carnaval.",
}

SENDA_FINISH: Dict[str, Any] = {
    "name": "Fuente de la Transparencia / Glorieta Torobajo",
    "coordinates": [1.2330, -77.2845],
    "address": "Avenida de los Estudiantes con Glorieta Torobajo",
    "description": "Punto de culminación oficial del desfile y llegada a la zona de desconcentración en Torobajo.",
}

# Strict Senda sequential path coordinates strictly in [latitude, longitude] format
SENDA_OFFICIAL_PATH: List[List[float]] = [
    [1.2025, -77.2762],  # Estadio Libertad (Salida)
    [1.2058, -77.2766],  # Cra 4
    [1.2095, -77.2770],  # Glorieta Lorenzo de Aldana
    [1.2115, -77.2778],  # Calle 19
    [1.2136, -77.2785],  # Plaza del Carnaval
    [1.2140, -77.2782],  # Cra 27
    [1.2148, -77.2780],  # Plaza de Nariño
    [1.2185, -77.2798],  # Calle 18
    [1.2220, -77.2810],  # San Felipe
    [1.2260, -77.2825],  # Avenida de los Estudiantes
    [1.2295, -77.2838],  # Carrera 40
    [1.2330, -77.2845],  # Fuente de la Transparencia / Torobajo (Llegada)
]


# ---------------------------------------------------------------------------
# Comprehensive Verified Local Places Directory for San Juan de Pasto
# ---------------------------------------------------------------------------

PASTO_PLACES_DIRECTORY: List[Dict[str, Any]] = [
    # ------------------ Baños Públicos (bathroom) ------------------
    {
        "name": "Batería San Agustín",
        "category": "bathroom",
        "coordinates": [1.2138, -77.2779],
        "address": "Calle 19 con Carrera 24, cerca al Templo San Agustín",
        "description": "Batería de baños públicos habilitada con personal de aseo y vigilancia permanente.",
    },
    {
        "name": "Baños Plaza del Carnaval",
        "category": "bathroom",
        "coordinates": [1.2132, -77.2783],
        "address": "Parqueadero subterráneo Plaza del Carnaval",
        "description": "Batería sanitaria amplia subterránea con acceso a rampas y cabinas múltiples.",
    },
    {
        "name": "Baños Estadio Libertad",
        "category": "bathroom",
        "coordinates": [1.2028, -77.2765],
        "address": "Costado Occidental Estadio Departamental Libertad",
        "description": "Servicios sanitarios de la zona sur habilitados durante el inicio de los desfiles.",
    },
    {
        "name": "Baños Plaza de Nariño",
        "category": "bathroom",
        "coordinates": [1.2149, -77.2783],
        "address": "Casa de Don Lorenzo, Carrera 26 con Calle 19",
        "description": "Módulos sanitarios céntricos ubicados a pocos metros del monumento a Nariño.",
    },

    # ------------------ Seguridad y CAIs (cai) ------------------
    {
        "name": "CAI Plaza de Nariño",
        "category": "cai",
        "coordinates": [1.2144, -77.2788],
        "address": "Centro Histórico, esquina noroccidental Plaza de Nariño",
        "description": "Atención policial inmediata, cuadrante centro histórico, recepción de denuncias y niños extraviados.",
    },
    {
        "name": "CAI Lorenzo de Aldana",
        "category": "cai",
        "coordinates": [1.2092, -77.2768],
        "address": "Glorieta Lorenzo de Aldana con Carrera 4",
        "description": "Puesto de control policial del sector sur para seguridad del primer tramo de la Senda.",
    },
    {
        "name": "CAI Morasurco",
        "category": "cai",
        "coordinates": [1.2298, -77.2835],
        "address": "Entrada Norte, Avenida Santander / Panamericana",
        "description": "Puesto policial del sector norte para apoyo y vigilancia en la Avenida de los Estudiantes y Torobajo.",
    },

    # ------------ Puestos de Salud y Primeros Auxilios (health) ------------
    {
        "name": "Puesto Cruz Roja Plaza Carnaval",
        "category": "health",
        "coordinates": [1.2130, -77.2781],
        "address": "Esquina Carrera 27 con Plaza del Carnaval",
        "description": "Carpa de triage, atención prehospitalaria, ambulancia medicalizada y voluntarios de la Cruz Roja.",
    },
    {
        "name": "Puesto Defensa Civil San Felipe",
        "category": "health",
        "coordinates": [1.2180, -77.2800],
        "address": "Calle 18 con Carrera 27, sector San Felipe",
        "description": "Puesto de socorro de la Defensa Civil, hidratación, primeros auxilios y evacuación de emergencias.",
    },
    {
        "name": "Hospital Departamental de Nariño",
        "category": "health",
        "coordinates": [1.2080, -77.2750],
        "address": "Calle 16 # 27-02, Sector Hospitalario Sur",
        "description": "Centro hospitalario de tercer nivel de urgencias y traumatología de alta complejidad.",
    },

    # ---------------- Restaurantes y Cafés Típicos (restaurant) ----------------
    {
        "name": "Restaurante El Paisano / Asadero",
        "category": "restaurant",
        "coordinates": [1.2190, -77.2802],
        "address": "Sector San Felipe, Calle 18 # 26-45",
        "description": "Restaurante típico tradicional de cuy asado, cerdo al horno, empanadas de añejo y lapingachos.",
    },
    {
        "name": "Cafetería La Merced",
        "category": "restaurant",
        "coordinates": [1.2150, -77.2786],
        "address": "Calle 18 cerca a Plaza de Nariño",
        "description": "Café tradicional con quimbolitos, café nariñense de altura, pasteles de hojaldre y bebidas calientes.",
    },
    {
        "name": "Zona Gastronómica Avenida de los Estudiantes",
        "category": "restaurant",
        "coordinates": [1.2270, -77.2828],
        "address": "Avenida de los Estudiantes entre Calles 19 y 22",
        "description": "Corredor gastronómico con asaderos, piqueteaderos, comidas rápidas y heladerías abiertas todo el desfile.",
    },

    # -------------------- Tarimas y Plazas (stage) --------------------
    {
        "name": "Tarima Oficial Plaza del Carnaval",
        "category": "stage",
        "coordinates": [1.2136, -77.2785],
        "address": "Plaza del Carnaval y la Cultura",
        "description": "Escenario principal de orquestas nacionales e internacionales, murgas y premiaciones del Carnaval.",
    },
    {
        "name": "Tarima de la Danza y Tradición Plaza de Nariño",
        "category": "stage",
        "coordinates": [1.2148, -77.2780],
        "address": "Plaza de Nariño, Centro Histórico",
        "description": "Escenario cultural para danzas autóctonas, agrupaciones andinas y poesía costumbrista nariñense.",
    },
    {
        "name": "Tarima del Carrizal",
        "category": "stage",
        "coordinates": [1.2225, -77.2815],
        "address": "Avenida Mijitayo / Sector El Carrizal",
        "description": "Escenario alternativo de son sureño, música campesina tradicional y colectivos juveniles.",
    },

    # ------------------ Centros Comerciales (shopping) ------------------
    {
        "name": "Centro Comercial Sebastián de Belalcázar",
        "category": "shopping",
        "coordinates": [1.2160, -77.2765],
        "address": "Calle 19 # 23-40, Centro",
        "description": "Centro comercial céntrico con cajeros automáticos, farmacias, telefonía e insumos carnavaleros.",
    },
    {
        "name": "Centro Comercial Unicentro Pasto",
        "category": "shopping",
        "coordinates": [1.2285, -77.2835],
        "address": "Avenida Panamericana con Calle 22, Norte",
        "description": "Gran complejo comercial con plazoleta de comidas, supermercado, parqueaderos y bancos.",
    },

    # ------------- Zonas de Riesgo / Aglomeración (risk_zone) -------------
    {
        "name": "Embudo Carrera 27 con Plaza del Carnaval",
        "category": "risk_zone",
        "coordinates": [1.2135, -77.2788],
        "address": "Carrera 27 intersección Calle 19, Plaza del Carnaval",
        "description": "Zona de cuello de botella peatonal y alta aglomeración durante el paso de carrozas monumentales. Cuide a menores y objetos personales.",
    },
]

# Alias for backwards compatibility
NEARBY_SERVICE_POINTS: List[Dict[str, Any]] = PASTO_PLACES_DIRECTORY


# ---------------------------------------------------------------------------
# Spatial Proximity Locator Engine
# ---------------------------------------------------------------------------

CATEGORY_ALIASES: Dict[str, str] = {
    "bathroom": "bathroom",
    "baño": "bathroom",
    "baños": "bathroom",
    "restroom": "bathroom",
    "sanitario": "bathroom",
    "sanitarios": "bathroom",
    "cai": "cai",
    "police": "cai",
    "policia": "cai",
    "policía": "cai",
    "seguridad": "cai",
    "health": "health",
    "salud": "health",
    "cruz roja": "health",
    "hospital": "health",
    "restaurant": "restaurant",
    "restaurante": "restaurant",
    "restaurantes": "restaurant",
    "comida": "restaurant",
    "cuy": "restaurant",
    "cafe": "restaurant",
    "café": "restaurant",
    "stage": "stage",
    "tarima": "stage",
    "tarimas": "stage",
    "concierto": "stage",
    "musica": "stage",
    "música": "stage",
    "shopping": "shopping",
    "comercial": "shopping",
    "risk_zone": "risk_zone",
    "riesgo": "risk_zone",
    "aglomeracion": "risk_zone",
}


def get_nearest_pois(
    user_lat: float,
    user_lng: float,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Calculate Haversine distance, sort from closest to furthest, and attach proximity labels.

    Args:
        user_lat: User real-time GPS latitude.
        user_lng: User real-time GPS longitude.
        category: Optional category filter (e.g. 'bathroom', 'cai', 'health', 'restaurant', 'stage').

    Returns:
        Sorted list of POIs with 'distance_meters' and human-readable 'proximity_label'.
    """
    target_category = None
    if category:
        norm_cat = category.lower().strip()
        target_category = CATEGORY_ALIASES.get(norm_cat, norm_cat)

    enriched_pois: List[Dict[str, Any]] = []

    for poi in PASTO_PLACES_DIRECTORY:
        poi_cat = poi.get("category", "")
        # Filter if category was requested
        if target_category and poi_cat != target_category:
            # Also allow fallback if category was 'police' and poi_cat is 'cai', or 'restroom' vs 'bathroom'
            if target_category == "bathroom" and poi_cat != "bathroom" and poi_cat != "restroom":
                continue
            elif target_category == "cai" and poi_cat != "cai" and poi_cat != "police":
                continue
            elif target_category != poi_cat:
                continue

        coords = poi["coordinates"]
        dist = calculate_distance_meters(user_lat, user_lng, coords[0], coords[1])
        label = format_proximity_label(dist)

        poi_copy = dict(poi)
        poi_copy["distance_meters"] = dist
        poi_copy["proximity_label"] = label
        enriched_pois.append(poi_copy)

    # Sort from nearest to furthest
    enriched_pois.sort(key=lambda p: p["distance_meters"])
    return enriched_pois


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
