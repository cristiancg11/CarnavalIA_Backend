"""Domain service for streaming and orchestrating carnival route telemetry."""
from datetime import datetime, timezone
import time
from typing import Any, Dict, Generator, List, Optional
from app.services.oop.base_gis import BaseGISService


class TelemetryStreamer:
    """Streams georeferenced telemetry points sequentially along the Senda del Carnaval."""

    # Curated landmark metadata matching each sequential point along the Senda
    WAYPOINT_METADATA: List[Dict[str, str]] = [
        {"name": "Estadio Departamental Libertad", "street": "Calle 2 con Carrera 4 (Salida Sur)"},
        {"name": "Carrera 4 - Sector Sur", "street": "Carrera 4 subiendo hacia Lorenzo"},
        {"name": "Glorieta Lorenzo de Aldana", "street": "Glorieta Lorenzo con Carrera 4"},
        {"name": "Calle 19", "street": "Calle 19 bajando hacia Plaza del Carnaval"},
        {"name": "Plaza del Carnaval y la Cultura", "street": "Plaza del Carnaval / Concha Acústica"},
        {"name": "Conexión Carrera 27", "street": "Carrera 27 intersección Calle 19"},
        {"name": "Plaza de Nariño", "street": "Centro Histórico / Carrera 27 con Calle 19"},
        {"name": "Calle 18 - Centro Norte", "street": "Calle 18 hacia San Felipe"},
        {"name": "Sector San Felipe", "street": "Calle 18 con Carrera 27"},
        {"name": "Avenida de los Estudiantes", "street": "Carrera 40 con Calle 20"},
        {"name": "Avenida de los Estudiantes Norte", "street": "Avenida de los Estudiantes sector Morasurco"},
        {"name": "Fuente de la Transparencia / Torobajo", "street": "Avenida de los Estudiantes / Llegada Torobajo"},
    ]

    def __init__(self, gis_service: BaseGISService) -> None:
        """Initialize TelemetryStreamer with injected GIS service.

        Args:
            gis_service: Service providing route coordinates and calculations.
        """
        self._gis_service = gis_service
        self._route = self._gis_service.get_official_route()

    @property
    def total_waypoints(self) -> int:
        """Total number of route waypoints in the official path."""
        return len(self._route)

    def get_all_points(self) -> List[Dict[str, Any]]:
        """Retrieve all telemetry points formatted as structured dictionaries.

        Returns:
            List of telemetry point dictionaries.
        """
        points: List[Dict[str, Any]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for idx, coord in enumerate(self._route):
            meta = (
                self.WAYPOINT_METADATA[idx]
                if idx < len(self.WAYPOINT_METADATA)
                else {"name": f"Punto Senda #{idx + 1}", "street": "Senda del Carnaval"}
            )
            points.append({
                "sequence_index": idx + 1,
                "latitude": coord[0],
                "longitude": coord[1],
                "landmark_name": meta["name"],
                "street_reference": meta["street"],
                "timestamp": now_iso,
            })
        return points

    def stream_telemetry(
        self,
        interval_seconds: float = 0.0
    ) -> Generator[Dict[str, Any], None, None]:
        """Generator yielding telemetry points sequentially (simulating live GPS parade tracking).

        Args:
            interval_seconds: Optional sleep interval between points in seconds.

        Yields:
            Telemetry point dictionary.
        """
        points = self.get_all_points()
        for pt in points:
            if interval_seconds > 0.0:
                time.sleep(interval_seconds)
            yield pt
