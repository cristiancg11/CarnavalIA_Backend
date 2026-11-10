"""Domain manager for Points of Interest (POIs) using Object-Oriented design and Dependency Injection."""
from typing import Any, Dict, List, Optional
from app.services.oop.base_gis import BaseGISService
from app.services.carnaval_gis_data import PASTO_PLACES_DIRECTORY


class POIManager:
    """Manages verified points of interest along the carnival route with spatial proximity query capabilities."""

    def __init__(self, gis_service: BaseGISService, custom_directory: Optional[List[Dict[str, Any]]] = None) -> None:
        """Initialize POIManager using Dependency Injection for the GIS service.

        Args:
            gis_service: Service implementing BaseGISService contract for distance calculations.
            custom_directory: Optional custom list of POIs (defaults to PASTO_PLACES_DIRECTORY).
        """
        self._gis_service = gis_service
        self._directory = list(custom_directory) if custom_directory is not None else list(PASTO_PLACES_DIRECTORY)

    @property
    def gis_service(self) -> BaseGISService:
        """Injected GIS service instance."""
        return self._gis_service

    @property
    def total_count(self) -> int:
        """Total number of registered points of interest."""
        return len(self._directory)

    def get_all(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all registered POIs, optionally filtered by category.

        Args:
            category: Optional category filter string.

        Returns:
            List of POI dictionaries.
        """
        if not category:
            return [dict(poi) for poi in self._directory]
        normalized_cat = category.strip().lower()
        return [
            dict(poi) for poi in self._directory
            if poi.get("category", "").lower() == normalized_cat
        ]

    def find_nearest_pois(
        self,
        user_lat: float,
        user_lng: float,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Compute real-time distance from user coordinates to all matching POIs and sort ascending.

        Args:
            user_lat: Latitude of user GPS position.
            user_lng: Longitude of user GPS position.
            category: Optional category filter.
            limit: Maximum number of closest results to return.

        Returns:
            Sorted list of POIs with attached distance_meters and proximity_label.
        """
        candidates = self.get_all(category=category)
        enriched: List[Dict[str, Any]] = []

        for poi in candidates:
            coords = poi.get("coordinates", [0.0, 0.0])
            dist = self._gis_service.calculate_distance(user_lat, user_lng, coords[0], coords[1])
            proximity = self._gis_service.format_proximity(dist)

            poi_entry = dict(poi)
            poi_entry["distance_meters"] = dist
            poi_entry["proximity_label"] = proximity
            enriched.append(poi_entry)

        enriched.sort(key=lambda item: item["distance_meters"])
        return enriched[:limit]

    def get_closest_poi(
        self,
        user_lat: float,
        user_lng: float,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve the single closest point of interest to the provided coordinates.

        Args:
            user_lat: User latitude.
            user_lng: User longitude.
            category: Optional category filter.

        Returns:
            Closest POI dictionary with distance metrics, or None if no POIs exist.
        """
        results = self.find_nearest_pois(user_lat, user_lng, category=category, limit=1)
        return results[0] if results else None

