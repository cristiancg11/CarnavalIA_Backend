"""Servicio de Chatbot Inteligente para el Carnaval de Negros y Blancos de Pasto.
Redirige y expone las capacidades completas de RAG con Gemini 2.5 Flash desde chat_service.
"""
from app.services.chat_service import (
    generate_chat_response,
    build_full_rag_context,
    CARNIVAL_SCHEDULE_DATA,
    PASTO_RESTAURANTS_DATA,
)

__all__ = [
    "generate_chat_response",
    "build_full_rag_context",
    "CARNIVAL_SCHEDULE_DATA",
    "PASTO_RESTAURANTS_DATA",
]
