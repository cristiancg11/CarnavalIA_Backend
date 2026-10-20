"""Endpoints para la consulta y registro de Puntos de Interés (POI) del Carnaval."""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.point_of_interest import PointOfInterest
from app.schemas.point_of_interest import POICreate, POIResponse

router = APIRouter()


@router.post(
    "",
    response_model=POIResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
@router.post(
    "/",
    response_model=POIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo punto de interés",
    description="Registra un nuevo punto de interés (servicios médicos, seguridad, tarimas, etc.) en el mapa del Carnaval."
)
def create_poi(
    poi_in: POICreate,
    db: Session = Depends(get_db)
):
    """Crea y persiste un nuevo punto de interés en la base de datos."""
    db_poi = PointOfInterest(
        name=poi_in.name,
        category=poi_in.category,
        latitude=poi_in.latitude,
        longitude=poi_in.longitude,
        description=poi_in.description
    )
    db.add(db_poi)
    db.commit()
    db.refresh(db_poi)
    return db_poi


@router.get(
    "",
    response_model=List[POIResponse],
    include_in_schema=False
)
@router.get(
    "/",
    response_model=List[POIResponse],
    summary="Listar puntos de interés",
    description="Obtiene todos los puntos de interés registrados con opción de filtrado por categoría (Salud, Policia, Banio, Tarima, Salida)."
)
def list_pois(
    category: Annotated[Optional[str], Query(description="Filtrar por categoría (Salud, Policia, Banio, Tarima, Salida)")] = None,
    skip: Annotated[int, Query(ge=0, description="Paginación: registros a omitir")] = 0,
    limit: Annotated[int, Query(ge=1, le=500, description="Límite máximo de resultados")] = 100,
    db: Session = Depends(get_db)
):
    """Retorna la lista de puntos de interés aplicando los filtros opcionales."""
    query = db.query(PointOfInterest)
    if category is not None:
        query = query.filter(PointOfInterest.category == category)
    return query.offset(skip).limit(limit).all()


@router.get(
    "/{poi_id}",
    response_model=POIResponse,
    summary="Obtener punto de interés por ID",
    description="Retorna la información detallada de un punto de interés por su ID primario."
)
def get_poi(
    poi_id: int,
    db: Session = Depends(get_db)
):
    """Busca un punto de interés específico."""
    poi = db.query(PointOfInterest).filter(PointOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Punto de interés con ID {poi_id} no fue encontrado."
        )
    return poi
