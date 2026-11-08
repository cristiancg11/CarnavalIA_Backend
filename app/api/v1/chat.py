"""Router API para el motor conversacional inteligente de GuaneñaBot (v1).

Procesa solicitudes de chat cultural y emite respuestas con acciones de mapa deterministas.
"""
from fastapi import APIRouter, status

from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.guanena_service import process_guanena_chat

router = APIRouter(tags=["GuaneñaBot AI"])


@router.post(
    "/guanena",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar a GuaneñaBot con acciones de mapa",
    description="Procesa lenguaje natural de turistas y ciudadanos, devolviendo respuesta cultural y acciones de mapa deterministas."
)
@router.post(
    "/guanena/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def chat_guanena(request: ChatRequest) -> ChatResponse:
    """Recibe la solicitud en lenguaje natural, invoca el servicio y retorna la respuesta con código 200."""
    return process_guanena_chat(request)
