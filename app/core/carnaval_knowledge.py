"""Catálogo de Hitos y Puntos de Partida Oficiales del Carnaval de Negros y Blancos de Pasto.

Provee georreferenciación oficial para desfiles, hitos patrimoniales,
gastronomía tradicional, puestos de salud y servicios sanitarios.
"""
from typing import Any, Dict, List, Tuple

# ==============================================================================
# HITOS Y PUNTOS DE SALIDA OFICIALES DE CADA EVENTO DEL CARNAVAL
# ==============================================================================
CARNAVAL_EVENTS: Dict[str, Dict[str, Any]] = {
    "dec_28": {
        "event_date": "dec_28",
        "name": "Arcoíris en el Asfalto",
        "date_label": "28 de Diciembre",
        "start_coords": [1.2140, -77.2785],
        "start_location": "Calle 18 / Plaza del Carnaval",
        "description": "Jornada de arte efímero donde la ciudadanía pinta con tiza sobre el pavimento, celebrando la paz, la creatividad urbana y el cuidado del agua.",
        "category": "desfile"
    },
    "dec_31": {
        "event_date": "dec_31",
        "name": "Desfile de Años Viejos",
        "date_label": "31 de Diciembre",
        "start_coords": [1.2052, -77.2796],
        "start_location": "Senda Champagnat / Parque Bolívar",
        "description": "Desfile satírico y picaresco donde monigotes y viudas expresan el sentir popular y los acontecimientos del año que termina.",
        "category": "desfile"
    },
    "jan_02": {
        "event_date": "jan_02",
        "name": "Carnavalito",
        "date_label": "02 de Enero",
        "start_coords": [1.2138, -77.2782],
        "start_location": "Plaza del Carnaval",
        "description": "Semillero de la tradición donde los niños desfilan con mini-carrozas, comparsitas y danzas en homenaje a la Virgen de las Mercedes.",
        "category": "desfile"
    },
    "jan_03": {
        "event_date": "jan_03",
        "name": "Canto a la Tierra",
        "date_label": "03 de Enero",
        "start_coords": [1.2052, -77.2796],
        "start_location": "Senda Champagnat / Sur",
        "description": "Desfile monumental de Colectivos Coreográficos con miles de músicos y danzantes al ritmo de zampoñas y bombos andinos.",
        "category": "desfile"
    },
    "jan_04": {
        "event_date": "jan_04",
        "name": "Llegada de la Familia Castañeda",
        "date_label": "04 de Enero",
        "start_coords": [1.2052, -77.2796],
        "start_location": "Senda Champagnat / Sur",
        "description": "Recreación teatral callejera que da la bienvenida a propios y forasteros, conmemorando la pintoresca comitiva campesina de 1929.",
        "category": "desfile"
    },
    "jan_05": {
        "event_date": "jan_05",
        "name": "Día de Negros",
        "date_label": "05 de Enero",
        "start_coords": [1.2168, -77.2805],
        "start_location": "Plaza de Nariño",
        "description": "Conmemoración de la igualdad y la libertad mediante el fraternal juego de la 'pintica' de cosmético negro y tarimas musicales.",
        "category": "desfile"
    },
    "jan_06": {
        "event_date": "jan_06",
        "name": "Día de Blancos - Desfile Magno",
        "date_label": "06 de Enero",
        "start_coords": [1.2052, -77.2796],
        "start_location": "Senda Champagnat / Sur",
        "description": "La cumbre del Carnaval: majestuosas Carrozas Monumentales esculpidas por maestros artesanos, comparsas, murgas y juego con talco y carioca.",
        "category": "desfile"
    },
    "jan_07": {
        "event_date": "jan_07",
        "name": "Festival del Cuy y la Cultura Campesina",
        "date_label": "07 de Enero",
        "start_coords": [1.2020, -77.2910],
        "start_location": "Catambuco / Obonuco",
        "description": "Remate gastronómico en los corregimientos donde se saborea el auténtico cuy asado en vara con papas pastusas y ají de maní.",
        "category": "gastronomia"
    }
}

# ==============================================================================
# PUNTOS DE INTERÉS: SALUD, BAÑOS Y COMIDA TÍPICA
# ==============================================================================
EXTRA_POIS_KNOWLEDGE: Dict[str, Dict[str, Any]] = {
    # Puestos de Primeros Auxilios / Salud
    "salud_pmu_carnaval": {
        "name": "PMU Central - Plaza del Carnaval",
        "category": "salud",
        "coords": [1.2118, -77.2760],
        "description": "Puesto de Mando Unificado con ambulancias medicalizadas, paramédicos de Cruz Roja y Defensa Civil."
    },
    "salud_pmu_champagnat": {
        "name": "PMU Sur - Senda Champagnat",
        "category": "salud",
        "coords": [1.2052, -77.2796],
        "description": "Puesto de socorro y valoración médica en el punto de salida sur de la Senda."
    },
    "salud_hospital_san_pedro": {
        "name": "Hospital Universitario San Pedro",
        "category": "salud",
        "coords": [1.2220, -77.2790],
        "description": "Centro hospitalario de tercer nivel para atención de urgencias complejas."
    },
    # Baños públicos y baterías sanitarias
    "bano_plaza_carnaval": {
        "name": "Batería de Baños Públicos - Plaza del Carnaval",
        "category": "bano",
        "coords": [1.2112, -77.2768],
        "description": "Módulos sanitarios portátiles y desinfectados para uso ciudadano junto a las graderías."
    },
    "bano_plaza_narino": {
        "name": "Batería de Baños Públicos - Plaza de Nariño",
        "category": "bano",
        "coords": [1.2155, -77.2795],
        "description": "Zona de baterías sanitarias habilitadas en el centro histórico de la ciudad."
    },
    "bano_champagnat": {
        "name": "Batería de Baños - Salida Senda Champagnat",
        "category": "bano",
        "coords": [1.2055, -77.2800],
        "description": "Servicios sanitarios ubicados en el área de salida y concentración de artistas."
    },
    # Comida típica y gastronomía nariñense
    "comida_asadero_cuyquer": {
        "name": "Asadero Tradicional Cuyquer",
        "category": "comida",
        "coords": [1.2160, -77.2915],
        "description": "Asadero tradicional en Mijitayo especializado en cuy asado al carbón con ají de maní."
    },
    "comida_cabana_andina": {
        "name": "La Cabaña Andina (Empanadas de Añejo)",
        "category": "comida",
        "coords": [1.2145, -77.2780],
        "description": "Ícono del centro histórico junto a la Plaza de Nariño, célebre por sus crocantes empanadas de añejo y café."
    },
    "comida_festival_obonuco": {
        "name": "Festival Gastronómico del Cuy - Obonuco",
        "category": "comida",
        "coords": [1.1890, -77.2920],
        "description": "Plaza campestre de Obonuco con fogones tradicionales de cuy asado y chicha de maíz."
    }
}
