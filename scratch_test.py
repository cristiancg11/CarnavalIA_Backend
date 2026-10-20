import math
from typing import List, Dict, Any, Optional

def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_km * c

def generate_nav_route(
    start_lat: float,
    start_lng: float,
    target_name: str,
    target_coords: List[float]
) -> Dict[str, Any]:
    t_lat, t_lng = target_coords[0], target_coords[1]
    
    # Corridor waypoint interpolation following Pasto street grid
    # Waypoint 1: User pos
    points = [[round(start_lat, 5), round(start_lng, 5)]]
    
    # Waypoint 2: Turn towards target latitude
    mid_lat = round(start_lat + (t_lat - start_lat) * 0.45, 5)
    points.append([mid_lat, round(start_lng, 5)])
    
    # Waypoint 3: Move along street towards target longitude
    mid_lng = round(start_lng + (t_lng - start_lng) * 0.75, 5)
    points.append([mid_lat, mid_lng])
    
    # Waypoint 4: Approach street
    points.append([round(t_lat, 5), mid_lng])
    
    # Waypoint 5: Target destination
    points.append([round(t_lat, 5), round(t_lng, 5)])
    
    return {
        "type": "ROUTE",
        "target_name": target_name,
        "target_coords": [round(t_lat, 5), round(t_lng, 5)],
        "route_coords": points
    }

print("Test route:", generate_nav_route(1.2136, -77.2811, "Restaurante Cuyquer", [1.2160, -77.2915]))
