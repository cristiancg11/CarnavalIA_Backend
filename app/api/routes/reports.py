"""Router de Reportes Ciudadanos para el Carnaval de Pasto.

Permite registrar incidencias ciudadanas (seguridad, primeros auxilios, extravío, tráfico)
e insertarlas directamente en la tabla 'reports' de Supabase, además de consultar los reportes
activos para pintar en el mapa interactivo del frontend.
"""
from typing import Annotated, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
import jwt

from app.api.deps import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.db.supabase import supabase_client
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportResponse
from app.services.ai_service import analyze_report_risk

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
@router.post(
    "/",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reporte ciudadano en Supabase",
    description="Recibe título, categoría (seguridad, primeros auxilios, extravío, tráfico), descripción, coordenadas y timestamp; lo inserta directamente en la tabla reports de Supabase."
)
def create_report(
    report_in: ReportCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Crea una incidencia ciudadana y la almacena en Supabase con análisis de riesgo."""
    # 1. Analizar nivel de riesgo preliminar con Gemini AI
    ai_result = analyze_report_risk(
        title=report_in.title,
        description=report_in.description or ""
    )
    ai_risk_level = ai_result.get("risk_level", "Bajo")

    # 2. Extraer user_id opcional de token Bearer JWT
    user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            sub = payload.get("sub")
            if sub:
                candidate_id = int(sub)
                user_record = db.query(User.id).filter(User.id == candidate_id).first()
                if user_record:
                    user_id = candidate_id
        except Exception:
            user_id = None

    # 3. Intentar inserción directa en Supabase vía cliente REST si está disponible
    inserted_via_rest = False
    rest_data = {
        "title": report_in.title,
        "description": report_in.description,
        "category": report_in.category,
        "latitude": report_in.latitude,
        "longitude": report_in.longitude,
        "ai_risk_level": ai_risk_level,
        "status": "Pendiente",
    }
    if user_id:
        rest_data["user_id"] = user_id

    try:
        if supabase_client.is_available:
            rest_response = supabase_client.table("reports").insert(rest_data).execute()
            if rest_response and hasattr(rest_response, "data") and rest_response.data:
                inserted_via_rest = True
    except Exception:
        inserted_via_rest = False

    # 4. Inserción garantizada en Supabase vía SQLAlchemy Session / Pooler de PostgreSQL
    db_report = Report(
        title=report_in.title,
        description=report_in.description,
        category=report_in.category,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        ai_risk_level=ai_risk_level,
        user_id=user_id,
        status="Pendiente"
    )

    try:
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
    except Exception as exc:
        db.rollback()
        # Fallback de clave foránea si el usuario no existe en la BD
        if db_report.user_id is not None:
            db_report.user_id = None
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al registrar reporte en Supabase: {str(exc)}"
            )

    return db_report


@router.get(
    "",
    response_model=List[ReportResponse],
    include_in_schema=False
)
@router.get(
    "/",
    response_model=List[ReportResponse],
    summary="Listar reportes activos en Supabase",
    description="Retorna los reportes activos (no descartados) para pintar marcadores en el mapa interactivo del frontend."
)
def list_active_reports(
    category: Annotated[Optional[str], Query(description="Filtrar por categoría (seguridad, primeros auxilios, extravío, tráfico)")] = None,
    status_filter: Annotated[Optional[str], Query(alias="status", description="Filtrar por estado específico")] = None,
    skip: Annotated[int, Query(ge=0, description="Número de registros a omitir")] = 0,
    limit: Annotated[int, Query(ge=1, le=500, description="Límite de reportes a retornar")] = 100,
    db: Session = Depends(get_db)
):
    """Consulta los reportes activos en la tabla reports de Supabase."""
    query = db.query(Report)

    # Filtrar por estado activo (excluyendo reportes descartados por defecto)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    else:
        query = query.filter(Report.status.in_(["Pendiente", "En_Revision", "Atendido"]))

    # Filtro opcional de categoría
    if category:
        query = query.filter(Report.category.ilike(f"%{category}%"))

    reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
    return reports


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Obtener detalle de reporte por ID",
    description="Retorna un reporte específico por su ID único."
)
def get_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un reporte ciudadano individual."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporte con ID {report_id} no encontrado en Supabase."
        )
    return report
