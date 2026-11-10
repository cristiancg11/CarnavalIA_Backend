"""Concrete implementation of BaseGISService utilizing the Haversine trigonometric formula."""
import math
from typing import List
from app.services.oop.base_gis import BaseGISService
from app.services.carnaval_gis_data import SENDA_OFFICIAL_PATH


class HaversineGISService(BaseGISService):
    """Geodetic service implementing great-circle distance computations via Haversine."""

    EARTH_RADIUS_METERS: float = 6371000.0

    def __init__(self, earth_radius_meters: float = EARTH_RADIUS_METERS) -> None:
        """Initialize Haversine service with configured planetary radius.

        Args:
            earth_radius_meters: Radius of the sphere in meters (defaults to 6,371,000m).
        """
        self._earth_radius = earth_radius_meters

    @property
    def earth_radius(self) -> float:
        """Encapsulated getter for earth radius."""
        return self._earth_radius

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points on the sphere.

        Args:
            lat1: Latitude of origin point.
            lon1: Longitude of origin point.
            lat2: Latitude of destination point.
            lon2: Longitude of destination point.

        Returns:
            Calculated distance in meters rounded to 1 decimal point.
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(self._earth_radius * c, 1)

    def format_proximity(self, distance_meters: float) -> str:
        """Transform numerical distance into an intuitive pedestrian description.

        Args:
            distance_meters: Distance in meters.

        Returns:
            Pedestrian proximity descriptor string.
        """
        if distance_meters < 50.0:
            return "a unos pasos (menos de 50 m)"
        if distance_meters < 150.0:
            return f"a solo {int(distance_meters)} metros (1 cuadra)"
        if distance_meters < 300.0:
            return f"a {int(distance_meters)} metros (~2 cuadras)"
        if distance_meters < 600.0:
            return f"a {int(distance_meters)} metros (~4-5 cuadras)"
        if distance_meters < 1000.0:
            return f"a {int(distance_meters)} metros (~8 cuadras)"
        km = round(distance_meters / 1000.0, 1)
        return f"a {km} km de distancia"

    def get_official_route(self) -> List[List[float]]:
        """Return the official Senda del Carnaval sequential polyline waypoints.

        Returns:
            List of [latitude, longitude] pairs.
        """
        return [list(coord) for coord in SENDA_OFFICIAL_PATH]
