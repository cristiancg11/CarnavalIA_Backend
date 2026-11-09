"""Pydantic schemas for CarnavalIA chat and GIS route extraction."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CarnavalChatRequest(BaseModel):
    """Request payload for GuaneñaBot Carnaval chat endpoint."""
    message: str = Field(..., min_length=1, description="User prompt or question in natural language.")
    history: Optional[List[Dict[str, str]]] = Field(
        default=[],
        description="Optional conversation history list of role-content message turns."
    )


class CarnavalChatResponse(BaseModel):
    """Response payload containing cultural response and GIS waypoints for Leaflet/OSRM."""
    reply: str = Field(..., description="Culturally authentic conversational response from GuaneñaBot.")
    should_draw_route: bool = Field(..., description="Flag indicating whether a route or landmark should be rendered on map.")
    waypoints: List[List[float]] = Field(default=[], description="List of [latitude, longitude] pairs for map navigation.")
    suggested_questions: List[str] = Field(default=[], description="Follow-up quick prompt questions.")
