"""Servicio de Inteligencia Artificial utilizando Google Gemini para CarnavalIA."""
import json
import logging
from typing import Dict, Any
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

# Categorías y niveles válidos
VALID_RISK_LEVELS = {"Bajo", "Medio", "Alto"}
VALID_CATEGORIES = {
    "Aglomeracion",
    "Emergencia",
    "Calle_Bloqueada",
    "Persona_Perdida",
    "Objeto_Perdido",
    "Riesgo",
}

DEFAULT_FALLBACK_ANALYSIS: Dict[str, Any] = {
    "risk_level": "Bajo",
    "suggested_category": "Riesgo",
    "summary": "Reporte registrado (análisis de IA no disponible o en modo sin conexión)."
}


def analyze_report_risk(title: str, description: str) -> Dict[str, Any]:
    """Analiza el título y la descripción de un reporte ciudadano del Carnaval

    de Negros y Blancos de Pasto utilizando el modelo gemini-2.5-flash.

    Retorna un diccionario con:
    - risk_level: "Bajo", "Medio" o "Alto"
    - suggested_category: una de las categorías válidas del carnaval
    - summary: Resumen conciso de 1 oración
    """
    # Si no hay clave de API configurada, retornar fallback sin lanzar excepción
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "" or settings.GEMINI_API_KEY == "tu_clave_de_gemini_aqui":
        logger.warning("GEMINI_API_KEY no configurada. Usando evaluación de riesgo por defecto ('Bajo').")
        return DEFAULT_FALLBACK_ANALYSIS.copy()

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""
Actúa como un analista de seguridad y logística experto para el Carnaval de Negros y Blancos de Pasto, Colombia.
Evalúa el siguiente reporte ciudadano de una incidencia en la senda del carnaval o la ciudad:

Título: {title}
Descripción: {description or 'Sin descripción adicional'}

Determina la criticidad y categorización. Debes responder con un JSON que contenga exactamente estos campos:
1. "risk_level": Estrictamente uno de estos tres valores: "Bajo", "Medio", "Alto".
2. "suggested_category": Estrictamente una de estas opciones: "Aglomeracion", "Emergencia", "Calle_Bloqueada", "Persona_Perdida", "Objeto_Perdido", "Riesgo".
3. "summary": Un resumen claro y conciso de la situación en 1 sola oración en español.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )

        if not response or not response.text:
            logger.warning("Respuesta vacía recibida de Gemini. Usando fallback.")
            return DEFAULT_FALLBACK_ANALYSIS.copy()

        result = json.loads(response.text.strip())

        # Validaciones y normalización de salida
        risk_level = result.get("risk_level", "Bajo")
        if risk_level not in VALID_RISK_LEVELS:
            risk_level = "Bajo"

        suggested_category = result.get("suggested_category", "Riesgo")
        if suggested_category not in VALID_CATEGORIES:
            suggested_category = "Riesgo"

        summary = result.get("summary", title)

        return {
            "risk_level": risk_level,
            "suggested_category": suggested_category,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Error al analizar el reporte con Gemini: {e}")
        # Nunca tumbamos el servidor si la API externa falla
        return DEFAULT_FALLBACK_ANALYSIS.copy()
