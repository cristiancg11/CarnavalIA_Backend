"""Script de carga inicial y actualización de datos geográficos (Seeder) para el Carnaval de Negros y Blancos de Pasto."""
import os
import sys

# Asegurar backend en sys.path para ejecución directa
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import logging
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from app.core.database import SessionLocal, engine, Base
from app.models.point_of_interest import PointOfInterest, POICategory
from app.models.zone_risk import ZoneRisk, RiskLevel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CARNAVAL_PASTO_POIS = [
    # 1. Puestos de Salud / Cruz Roja
    {
        "name": "Puesto de Salud Cruz Roja - Plaza del Carnaval",
        "category": POICategory.SALUD.value,
        "latitude": 1.2115,
        "longitude": -77.2785,
        "description": "Atención prehospitalaria, ambulancia y primeros auxilios en la Plaza del Carnaval y de la Cultura."
    },
    {
        "name": "Puesto de Salud y Triaje - Plaza de Nariño",
        "category": POICategory.SALUD.value,
        "latitude": 1.2145,
        "longitude": -77.2782,
        "description": "Atención médica inmediata, paramédicos y carpa de la Cruz Roja Seccional Nariño."
    },
    {
        "name": "Módulo de Atención Médica - Parque Infantil",
        "category": POICategory.SALUD.value,
        "latitude": 1.2205,
        "longitude": -77.2850,
        "description": "Unidad de estabilización y respuesta rápida para asistentes al desfile."
    },
    {
        "name": "Puesto de Salud - Senda Av. Los Estudiantes",
        "category": POICategory.SALUD.value,
        "latitude": 1.2250,
        "longitude": -77.2885,
        "description": "Puesto de socorro y ambulancia de alta complejidad en el sector norte de la senda."
    },

    # 2. CAI y Puntos Policiales
    {
        "name": "CAI Móvil Policía Nacional - Parque Infantil",
        "category": POICategory.POLICIA.value,
        "latitude": 1.2202,
        "longitude": -77.2848,
        "description": "Puesto de mando policial, recepción de denuncias y control del orden público."
    },
    {
        "name": "Puesto de Control Policial - Carrera 27 con Calle 17",
        "category": POICategory.POLICIA.value,
        "latitude": 1.2130,
        "longitude": -77.2798,
        "description": "Vigilancia en el corredor de la Carrera 27 para desfile de carrozas y murgas."
    },
    {
        "name": "Puesto de Seguridad y Monitoreo - Plaza del Carnaval",
        "category": POICategory.POLICIA.value,
        "latitude": 1.2118,
        "longitude": -77.2788,
        "description": "Monitoreo con cámaras de seguridad y patrullaje motorizado continuo."
    },
    {
        "name": "CAI Central - Plaza de Nariño",
        "category": POICategory.POLICIA.value,
        "latitude": 1.2148,
        "longitude": -77.2780,
        "description": "Puesto de atención ciudadana y apoyo de Policía de Turismo."
    },

    # 3. Tarimas de Orquestas y Escenarios
    {
        "name": "Tarima Principal del Carnaval - Plaza del Carnaval",
        "category": POICategory.TARIMA.value,
        "latitude": 1.2112,
        "longitude": -77.2782,
        "description": "Escenario principal de conciertos, orquestas nacionales e internacionales y premiación de comparsas."
    },
    {
        "name": "Tarima de Música Campesina y Andina - Plaza de Nariño",
        "category": POICategory.TARIMA.value,
        "latitude": 1.2142,
        "longitude": -77.2786,
        "description": "Escenario para grupos andinos, tríos tradicionales y música nariñense."
    },
    {
        "name": "Tarima Cultural y Artística - Parque Infantil",
        "category": POICategory.TARIMA.value,
        "latitude": 1.2208,
        "longitude": -77.2853,
        "description": "Espacio musical alternativo y zona de descanso para las agrupaciones del desfile."
    },

    # 4. Puntos de Baños Públicos
    {
        "name": "Batería de Baños Públicos - Plaza del Carnaval (Costado Sur)",
        "category": POICategory.BANIO.value,
        "latitude": 1.2108,
        "longitude": -77.2783,
        "description": "Batería de servicios sanitarios públicos portátiles con mantenimiento permanente."
    },
    {
        "name": "Batería de Baños - Carrera 27 (Sector Bomboná)",
        "category": POICategory.BANIO.value,
        "latitude": 1.2125,
        "longitude": -77.2792,
        "description": "Batería de baños higiénicos sobre la Senda del Carnaval."
    },
    {
        "name": "Baños Públicos Plaza de Nariño (Calle 19)",
        "category": POICategory.BANIO.value,
        "latitude": 1.2147,
        "longitude": -77.2788,
        "description": "Servicios higiénicos accesibles y señalizados para el público general."
    },
    {
        "name": "Batería de Baños Públicos - Parque Infantil",
        "category": POICategory.BANIO.value,
        "latitude": 1.2200,
        "longitude": -77.2855,
        "description": "Servicios sanitarios portátiles en el costado oriental del Parque Infantil."
    },
    {
        "name": "Baños Públicos - Senda Av. Los Estudiantes",
        "category": POICategory.BANIO.value,
        "latitude": 1.2248,
        "longitude": -77.2882,
        "description": "Batería de baños disponibles en el sector norte de la senda."
    },

    # 5. Salidas y Rutas de Evacuación
    {
        "name": "Ruta de Evacuación Calle 18 hacia Cra 25",
        "category": POICategory.SALIDA.value,
        "latitude": 1.2138,
        "longitude": -77.2770,
        "description": "Vía despejada de salida rápida hacia el oriente de Pasto libre de vallas."
    },
    {
        "name": "Ruta de Evacuación Emergencias Calle 20 hacia Cra 30",
        "category": POICategory.SALIDA.value,
        "latitude": 1.2155,
        "longitude": -77.2810,
        "description": "Corredor de seguridad exclusivo para ambulancias y vehículos de respuesta rápida."
    },
]

INITIAL_ZONES = [
    {
        "zone_name": "Plaza del Carnaval",
        "congestion_percentage": 78.0,
        "risk_level": "Alto"
    },
    {
        "zone_name": "Plaza de Nariño",
        "congestion_percentage": 55.0,
        "risk_level": "Medio"
    },
    {
        "zone_name": "Parque Infantil",
        "congestion_percentage": 40.0,
        "risk_level": "Medio"
    },
    {
        "zone_name": "Senda Avenida Los Estudiantes",
        "congestion_percentage": 20.0,
        "risk_level": "Bajo"
    },
]


def seed_carnaval_data(db: Session, force_refresh: bool = False) -> None:
    """Inserta o actualiza los puntos de interés reales en Pasto para el Carnaval."""
    # 1. Asegurar tablas creadas
    Base.metadata.create_all(bind=engine)

    # 2. Puntos de Interés
    existing_pois = db.query(PointOfInterest).all()
    if force_refresh or len(existing_pois) < len(CARNAVAL_PASTO_POIS):
        logger.info(f"Actualizando puntos de interés del Carnaval ({len(existing_pois)} actuales -> {len(CARNAVAL_PASTO_POIS)} nuevos)...")
        # Eliminar existentes para evitar duplicados en seed
        db.execute(delete(PointOfInterest))
        for poi_data in CARNAVAL_PASTO_POIS:
            db.add(PointOfInterest(**poi_data))
        db.commit()
        logger.info(f"Puntos de interés sembrados exitosamente: {len(CARNAVAL_PASTO_POIS)} registros.")
    else:
        logger.info(f"La tabla points_of_interest ya contiene {len(existing_pois)} registros.")

    # 3. Zonas de riesgo iniciales
    for zone_data in INITIAL_ZONES:
        existing_zone = db.query(ZoneRisk).filter(ZoneRisk.zone_name == zone_data["zone_name"]).first()
        if not existing_zone:
            db.add(ZoneRisk(**zone_data))
        else:
            existing_zone.congestion_percentage = zone_data["congestion_percentage"]
            existing_zone.risk_level = zone_data["risk_level"]
    db.commit()
    logger.info("Zonas de riesgo sembradas y sincronizadas exitosamente.")


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_carnaval_data(session, force_refresh=True)
        print("¡Seeder de CarnavalIA ejecutado con éxito en la base de datos de Supabase!")
