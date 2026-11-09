"""Pydantic schemas for CarnavalIA chat and GIS route extraction."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CarnavalSchedule(BaseModel):
    """Carnival parade or event timing and locations."""
    start_time: str = Field(..., description="Scheduled departure time (e.g. '10:00 AM').")
    estimated_arrival_time: str = Field(..., description="Estimated arrival or finish time (e.g. '3:30 PM').")
    start_location: str = Field(..., description="Starting point or muster plaza.")
    finish_location: str = Field(..., description="Final terminus or dispersal plaza.")
    event_name: Optional[str] = Field(default=None, description="Official carnival day or parade title.")


class NearbyPlace(BaseModel):
    """Strategic urban service point or crowd-risk zone along the Senda."""
    name: str = Field(..., description="Official title or label of the landmark.")
    category: str = Field(..., description="Category: restroom, police, health, stage, restaurant, shopping, risk_zone.")
    coordinates: List[float] = Field(..., description="[latitude, longitude] geographic coordinates.")
    description: Optional[str] = Field(default="", description="Service details, triage capability, or safety warning.")


class CarnavalChatRequest(BaseModel):
    """Request payload for GuaneñaBot Carnaval chat endpoint."""
    message: str = Field(..., min_length=1, description="User prompt or question in natural language.")
    history: Optional[List[Dict[str, str]]] = Field(
        default=[],
        description="Optional conversation history list of role-content message turns."
    )


class CarnavalChatResponse(BaseModel):
    """Response payload containing cultural response, schedule, GIS route, and telemetry layers."""
    reply: str = Field(..., description="Culturally authentic conversational response from GuaneñaBot.")
    schedule: Optional[CarnavalSchedule] = Field(
        default=None,
        description="Schedule estimates including start/end times and locations."
    )
    should_draw_route: bool = Field(..., description="Flag indicating whether a route or landmark should be rendered on map.")
    route_coordinates: List[List[float]] = Field(
        default=[],
        description="Ordered list of [latitude, longitude] pairs for Leaflet Polyline navigation."
    )
    waypoints: List[List[float]] = Field(
        default=[],
        description="Alias of route_coordinates for backward compatibility."
    )
    nearby_places: List[NearbyPlace] = Field(
        default=[],
        description="List of nearby public services, safety points, and risk zones."
    )
    suggested_questions: List[str] = Field(
        default=[],
        description="Follow-up quick prompt questions."
    )
