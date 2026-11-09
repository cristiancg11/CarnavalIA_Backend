"""Spatial geodesy utilities for real-time GPS distance and proximity calculations."""
import math


def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two geographic points in meters using Haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)


def format_proximity_label(distance_meters: float) -> str:
    """Return a human-friendly Spanish proximity description based on meters."""
    if distance_meters < 50:
        return "a unos pasos (menos de 50 m)"
    if distance_meters < 150:
        return f"a solo {int(distance_meters)} metros (1 cuadra)"
    if distance_meters < 300:
        return f"a {int(distance_meters)} metros (~2 cuadras)"
    if distance_meters < 600:
        return f"a {int(distance_meters)} metros (~4-5 cuadras)"
    if distance_meters < 1000:
        return f"a {int(distance_meters)} metros (~8 cuadras)"
    km = round(distance_meters / 1000, 1)
    return f"a {km} km de distancia"
