"""Exportación centralizada de modelos ORM para CarnavalIA."""
from app.models.user import User
from app.models.report import Report, ReportCategory, ReportStatus
from app.models.point_of_interest import PointOfInterest, POICategory
from app.models.zone_risk import ZoneRisk, RiskLevel

__all__ = [
    "User",
    "Report",
    "ReportCategory",
    "ReportStatus",
    "PointOfInterest",
    "POICategory",
    "ZoneRisk",
    "RiskLevel",
]
