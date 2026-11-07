"""Endpoints de Reportes para API v1 alineados con la tabla reports de Supabase."""
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter()


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
    summary="Crear reporte ciudadano",
    description="Recibe title, category, description, latitude, longitude e inserta en la tabla reports de Supabase."
)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db)
):
    """Inserta un nuevo reporte en la tabla reports de Supabase y retorna el registro creado."""
    db_report = Report(
        title=report_in.title.strip(),
        category=report_in.category.strip(),
        description=report_in.description.strip() if report_in.description else None,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        status="Pendiente"
    )

    try:
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar reporte: {str(exc)}"
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
    summary="Listar todos los reportes",
    description="Consulta y retorna todos los registros de la tabla reports."
)
def list_reports(
    db: Session = Depends(get_db)
):
    """Consulta y retorna todos los registros de la tabla reports de Supabase."""
    return db.query(Report).order_by(Report.created_at.desc()).all()


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Obtener reporte por ID"
)
def get_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """Obtiene un reporte individual por su UUID."""
    try:
        report_uuid = uuid.UUID(report_id)
        report = db.query(Report).filter(Report.id == report_uuid).first()
    except ValueError:
        report = None

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporte con ID {report_id} no encontrado."
        )
    return report
