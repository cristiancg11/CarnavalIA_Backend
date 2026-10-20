"""Endpoints para el Chatbot Inteligente del Carnaval de Negros y Blancos."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chatbot_service import generate_chat_response

router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar al Asistente Virtual Oficial del Carnaval",
    description=(
        "Recibe una consulta ciudadana o turística junto con la ubicación geográfica opcional del usuario. "
        "Consulta la base de datos en tiempo real (puntos de interés, puestos de salud/seguridad y reportes recientes) "
        "y genera una respuesta contextualizada mediante Google Gemini (gemini-2.5-flash)."
    )
)
def chat_with_carnaval_assistant(
    chat_in: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """Procesa la pregunta del usuario, enriquece con la información en tiempo real de Pasto

    y retorna la respuesta orientativa generada por el Asistente Virtual.
    """
    lat = chat_in.user_lat if chat_in.user_lat is not None else chat_in.user_latitude
    lng = chat_in.user_lng if chat_in.user_lng is not None else chat_in.user_longitude

    return generate_chat_response(
        message=chat_in.message,
        user_latitude=lat,
        user_longitude=lng,
        user_lat=lat,
        user_lng=lng,
        selected_day=chat_in.selected_day,
        db=db
    )

