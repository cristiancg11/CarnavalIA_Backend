"""Abstract Base GIS service definition following Object-Oriented principles."""
from abc import ABC, abstractmethod
from typing import List


class BaseGISService(ABC):
    """Abstract Base Class establishing the architectural contract for geospatial operations."""

    @abstractmethod
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters.

        Args:
            lat1: Latitude of origin point.
            lon1: Longitude of origin point.
            lat2: Latitude of destination point.
            lon2: Longitude of destination point.

        Returns:
            Distance in meters as a floating-point number.
        """
        pass

    @abstractmethod
    def format_proximity(self, distance_meters: float) -> str:
        """Format a meter distance into a human-readable proximity string.

        Args:
            distance_meters: Distance in meters.

        Returns:
            Human-readable proximity description.
        """
        pass

    @abstractmethod
    def get_official_route(self) -> List[List[float]]:
        """Retrieve sequential coordinate pairs representing the official carnival path.

        Returns:
            List of [latitude, longitude] pairs.
        """
        pass
