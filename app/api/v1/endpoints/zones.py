"""Endpoints para el monitoreo y cálculo dinámico de Zonas de Riesgo y Congestión."""
import math
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.report import Report
from app.models.zone_risk import ZoneRisk
from app.schemas.zone_risk import ZoneRiskResponse

router = APIRouter()

# Zonas principales de la Senda del Carnaval de San Juan de Pasto
MAIN_CARNAVAL_ZONES = [
    {
        "id": 1,
        "zone_name": "Plaza del Carnaval",
        "latitude": 1.2115,
        "longitude": -77.2785,
        "radius_meters": 280.0,
    },
    {
        "id": 2,
        "zone_name": "Plaza de Nariño",
        "latitude": 1.2145,
        "longitude": -77.2782,
        "radius_meters": 260.0,
    },
    {
        "id": 3,
        "zone_name": "Parque Infantil",
        "latitude": 1.2205,
        "longitude": -77.2850,
        "radius_meters": 300.0,
    },
    {
        "id": 4,
        "zone_name": "Senda Avenida Los Estudiantes",
        "latitude": 1.2250,
        "longitude": -77.2885,
        "radius_meters": 320.0,
    },
]


def _haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia geodésica en metros entre dos puntos geográficos usando Haversine."""
    earth_radius_m = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_m * c


@router.get(
    "/risk",
    response_model=List[ZoneRiskResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener niveles dinámicos de riesgo por zonas del Carnaval",
    description=(
        "Agrupa y calcula dinámicamente los niveles de riesgo acumulados a partir de los reportes "
        "de incidentes clasificados por IA (Gemini) en las zonas principales de la Senda del Carnaval "
        "(Plaza de Nariño, Plaza del Carnaval, Parque Infantil y Senda Central)."
    )
)
@router.get(
    "/risk/",
    response_model=List[ZoneRiskResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def get_zones_risk(
    db: Session = Depends(get_db)
) -> List[ZoneRiskResponse]:
    """Calcula el estado y criticidad de cada sector en tiempo real según reportes activos."""
    # 1. Consultar todos los reportes activos (Pendiente o En_Revision)
    active_reports = (
        db.query(Report)
        .filter(Report.status.in_(["Pendiente", "En_Revision"]))
        .all()
    )

    results: List[ZoneRiskResponse] = []

    # 2. Evaluar cada zona principal del Carnaval
    for zone in MAIN_CARNAVAL_ZONES:
        zone_reports = []
        for rep in active_reports:
            dist_m = _haversine_distance_meters(
                zone["latitude"], zone["longitude"],
                rep.latitude, rep.longitude
            )
            is_in_radius = dist_m <= zone["radius_meters"]
            text_match = zone["zone_name"].lower() in (
                (rep.title or "").lower() + " " + (rep.description or "").lower()
            )

            if is_in_radius or text_match:
                zone_reports.append(rep)

        reports_count = len(zone_reports)

        # 3. Determinar nivel de riesgo acumulado
        has_high_risk = any(r.ai_risk_level == "Alto" for r in zone_reports)
        has_medium_risk = any(r.ai_risk_level == "Medio" for r in zone_reports)

        if has_high_risk or reports_count >= 5:
            risk_level = "Alto"
        elif has_medium_risk or reports_count >= 2:
            risk_level = "Medio"
        else:
            risk_level = "Bajo"

        # 4. Sincronizar / persistir en la tabla ZoneRisk para el monitoreo global
        db_zone = db.query(ZoneRisk).filter(ZoneRisk.zone_name == zone["zone_name"]).first()
        congestion = min(100.0, reports_count * 20.0)

        if not db_zone:
            db_zone = ZoneRisk(
                zone_name=zone["zone_name"],
                congestion_percentage=congestion,
                risk_level=risk_level
            )
            db.add(db_zone)
        else:
            db_zone.congestion_percentage = congestion
            db_zone.risk_level = risk_level

        results.append(
            ZoneRiskResponse(
                id=zone["id"],
                zone_name=zone["zone_name"],
                risk_level=risk_level,
                congestion_percentage=congestion,
                active_reports_count=reports_count,
                latitude=zone["latitude"],
                longitude=zone["longitude"],
                radius_meters=zone["radius_meters"]
            )
        )

    db.commit()
    return results
