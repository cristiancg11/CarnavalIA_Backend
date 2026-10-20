"""Script de carga inicial de datos (Seeder) para el Carnaval de Negros y Blancos."""
import logging
from sqlalchemy.orm import Session
from app.models.point_of_interest import PointOfInterest, POICategory

logger = logging.getLogger(__name__)

INITIAL_POIS = [
    {
        "name": "Puesto de Salud Plaza de Nariño",
        "category": POICategory.SALUD.value,
        "latitude": 1.2136,
        "longitude": -77.2811,
        "description": "Atención médica básica, primeros auxilios y triaje en la Plaza de Nariño."
    },
    {
        "name": "Puesto de Salud Plaza del Carnaval",
        "category": POICategory.SALUD.value,
        "latitude": 1.2090,
        "longitude": -77.2770,
        "description": "Puesto de atención prehospitalaria y ambulancia en la Plaza del Carnaval."
    },
    {
        "name": "CAI de Policía Plaza de Nariño",
        "category": POICategory.POLICIA.value,
        "latitude": 1.2138,
        "longitude": -77.2815,
        "description": "Puesto de control, seguridad ciudadana y recepción de denuncias."
    },
    {
        "name": "Tarima Principal Plaza del Carnaval",
        "category": POICategory.TARIMA.value,
        "latitude": 1.2092,
        "longitude": -77.2773,
        "description": "Escenario principal para presentaciones artísticas, desfiles y orquestas."
    },
    {
        "name": "Baños Públicos Parque Infantil",
        "category": POICategory.BANIO.value,
        "latitude": 1.2180,
        "longitude": -77.2830,
        "description": "Batería de servicios sanitarios públicos habilitados para el Carnaval."
    },
]


from app.db.seed_carnaval import seed_carnaval_data, CARNAVAL_PASTO_POIS

def seed_points_of_interest(db: Session) -> None:
    """Inserta o sincroniza los puntos de interés iniciales si es necesario."""
    seed_carnaval_data(db, force_refresh=False)
