"""Servicio del Asistente Turístico y Cultural GuaneñaBot con Google Gemini y Fallback Determinista.

Procesa lenguaje natural de turistas y ciudadanos para responder con contexto cultural
y devolver acciones deterministas de mapa para el Carnaval de Negros y Blancos de Pasto.
"""
import json
import logging
import re
from typing import Any, Dict, Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.carnaval_knowledge import CARNAVAL_EVENTS, EXTRA_POIS_KNOWLEDGE
from app.schemas.chat_schema import ChatRequest, ChatResponse, MapAction

logger = logging.getLogger(__name__)

# ==============================================================================
# PROMPT DE SISTEMA OFICIAL DE GUANEÑABOT
# ==============================================================================
GUANENA_SYSTEM_PROMPT = """Eres GuaneñaBot, el asistente turístico y cultural oficial del Carnaval de Negros y Blancos en Pasto, Nariño. Eres cordial, conocedor y usas expresiones pastusas respetuosas ('¡Qué viva Pasto, carajo!', 'veci', 'guagua').
Cuando un usuario pregunte por un evento o dónde empieza un desfile (ej. 4 de enero / Familia Castañeda), debes:
1. Explicar brevemente la tradición del día (2 a 3 líneas).
2. Identificar el punto de partida exacto (generalmente Senda Champagnat al sur de la ciudad).
3. Devolver OBLIGATORIAMENTE un JSON con 'reply' y 'map_action' con action_type: 'ROUTE_TO_EVENT_START', target_name y sus target_coords.

Puntos de partida oficiales:
- 28 Dic (Arcoíris en el Asfalto): [1.2140, -77.2785] (Calle 18 / Plaza del Carnaval)
- 31 Dic (Años Viejos): [1.2052, -77.2796] (Senda Champagnat / Parque Bolívar)
- 02 Ene (Carnavalito): [1.2138, -77.2782] (Plaza del Carnaval)
- 03 Ene (Canto a la Tierra): [1.2052, -77.2796] (Senda Champagnat / Sur)
- 04 Ene (Familia Castañeda): [1.2052, -77.2796] (Senda Champagnat / Sur)
- 05 Ene (Día de Negros): [1.2168, -77.2805] (Plaza de Nariño)
- 06 Ene (Desfile Magno): [1.2052, -77.2796] (Senda Champagnat / Sur)
- 07 Ene (Festival del Cuy): [1.2020, -77.2910] (Catambuco / Obonuco)

Si el usuario consulta por comida típica (cuy, empanadas de añejo), salud/primeros auxilios o baños, responde cordialmente y emite el map_action correspondiente (ej. action_type: 'FILTER_POIS' o 'ROUTE_TO_EVENT_START' con sus coordenadas).
Si es una charla sin necesidad de mapa, map_action puede ser null o action_type 'INFO_ONLY'.
Debes responder ÚNICAMENTE un objeto JSON válido con las claves 'reply' y 'map_action'.
"""


def _parse_gemini_json_response(raw_text: str) -> Dict[str, Any]:
    """Limpia etiquetas de markdown y convierte la salida de Gemini a diccionario."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())


# ==============================================================================
# PARSER DE RESPALDO DETERMINISTA BASADO EN REGLAS CLÍNICAS Y CULTURALES
# ==============================================================================
def deterministic_guanena_fallback(message: str) -> ChatResponse:
    """Fallback local determinista que detecta intenciones mediante regex ante caídas de API."""
    msg = message.lower().strip()

    # 1. 04 de Enero / Familia Castañeda
    if re.search(r"(4\s*(de\s*)?ene|cuatro\s*de\s*enero|casta[ñn]eda)", msg):
        ev = CARNAVAL_EVENTS["jan_04"]
        return ChatResponse(
            reply=(
                "¡Qué viva Pasto, carajo, veci! El 4 de enero celebramos la emblemática Llegada de la Familia Castañeda, "
                "recreando la bienvenida a propios y forasteros con trajes campesinos de época y cuadros costumbristas de 1929. "
                "El desfile parte oficialmente desde la Senda Champagnat al sur de la ciudad y recorre toda la Senda hasta el centro."
            ),
            map_action=MapAction(
                action_type="ROUTE_TO_EVENT_START",
                target_name=f"Salida Familia Castañeda ({ev['start_location']})",
                target_coords=ev["start_coords"],
                event_date=ev["event_date"],
                category=ev["category"]
            )
        )

    # 2. 06 de Enero / Día de Blancos / Desfile Magno / Carrozas
    if re.search(r"(6\s*(de\s*)?ene|seis\s*de\s*enero|blanco|carroza|desfile\s*magno)", msg):
        ev = CARNAVAL_EVENTS["jan_06"]
        return ChatResponse(
            reply=(
                "¡Qué viva Pasto, carajo! El 6 de enero es el magno Día de Blancos, la máxima expresión estética de nuestro Carnaval. "
                "Podrá apreciar las colosales Carrozas Monumentales esculpidas por maestros artesanos, comparsas y murgas, mientras jugamos con cosmético blanco y carioca. "
                "La partida del desfile se realiza en la Senda Champagnat al sur de Pasto."
            ),
            map_action=MapAction(
                action_type="ROUTE_TO_EVENT_START",
                target_name=f"Salida Desfile Magno ({ev['start_location']})",
                target_coords=ev["start_coords"],
                event_date=ev["event_date"],
                category=ev["category"]
            )
        )

    # 3. 05 de Enero / Día de Negros / Pintica
    if re.search(r"(5\s*(de\s*)?ene|cinco\s*de\s*enero|negro|pintica)", msg):
        ev = CARNAVAL_EVENTS["jan_05"]
        return ChatResponse(
            reply=(
                "¡Una pintica por la paz, veci! El 5 de enero celebramos el Día de Negros, recordando la libertad y la igualdad con el fraternal juego de cosmético negro. "
                "En este día no hay desfile de carrozas gigantes, sino orquestas en vivo y gran gozo popular en las plazas principales. "
                "El epicentro de encuentro se concentra en la Plaza de Nariño y la Plaza del Carnaval."
            ),
            map_action=MapAction(
                action_type="ROUTE_TO_EVENT_START",
                target_name=f"Epicentro Día de Negros ({ev['start_location']})",
                target_coords=ev["start_coords"],
                event_date=ev["event_date"],
                category=ev["category"]
            )
        )

    # 4. 03 de Enero / Canto a la Tierra / Colectivos Coreográficos
    if re.search(r"(3\s*(de\s*)?ene|tres\s*de\s*enero|canto\s*a\s*la\s*tierra|colectivo)", msg):
        ev = CARNAVAL_EVENTS["jan_03"]
        return ChatResponse(
            reply=(
                "¡Fuerza andina en el Carnaval, veci! El 3 de enero vivimos el Desfile Canto a la Tierra con miles de músicos y danzantes "
                "de Colectivos Coreográficos que hacen vibrar el asfalto con sus quenas, zampoñas y trajes ceremoniales en homenaje a la Pacha Mama. "
                "La concentración e inicio se sitúa en la Senda Champagnat en el sur."
            ),
            map_action=MapAction(
                action_type="ROUTE_TO_EVENT_START",
                target_name=f"Salida Canto a la Tierra ({ev['start_location']})",
                target_coords=ev["start_coords"],
                event_date=ev["event_date"],
                category=ev["category"]
            )
        )

    # 5. 02 de Enero / Carnavalito
    if re.search(r"(2\s*(de\s*)?ene|dos\s*de\s*enero|carnavalito|ni[ñn]o|guagua)", msg):
        ev = CARNAVAL_EVENTS["jan_02"]
        return ChatResponse(
            reply=(
                "¡Qué emoción ver a nuestros guaguas, veci! El 2 de enero se celebra el Carnavalito, semillero de nuestra tradición donde los niños desfilan con sus mini-carrozas y comparsitas en devoción a la Virgen de las Mercedes. "
                "El punto oficial de salida y concentración es en la Plaza del Carnaval."
            ),
            map_action=MapAction(
                action_type="ROUTE_TO_EVENT_START",
                target_name=f"Salida Carnavalito ({ev['start_location']})",
                target_coords=ev["start_coords"],
                event_date=ev["event_date"],
                category=ev["category"]
            )
        )

    # 6. 28 de Diciembre / Arcoíris en el Asfalto
    if re.search(r"(28\s*(de\s*)?dic|veintiocho\s*de\s*diciembre|arco[ií]ris|asfalto|tiza|colorado)", msg):
        ev = CARNAVAL_EVENTS["dec_28"]
        return ChatResponse(
            reply=(
                "¡Arte efímero y amor por el agua, veci! El 28 de diciembre conmemoramos el Arcoíris en el Asfalto en el sector de El Colorado y la Calle 18, "
                "donde pintamos con tizas multicolores en el suelo como mensaje de paz y cultura ambiental. "
                "El epicentro de encuentro es en la Calle 18 junto a la Plaza del Carnaval."
            ),
            map_action=MapAction(
                action_type="ROUTE_TO_EVENT_START",
                target_name=f"Arcoíris en el Asfalto ({ev['start_location']})",
                target_coords=ev["start_coords"],
                event_date=ev["event_date"],
                category=ev["category"]
            )
        )

    # 7. 31 de Diciembre / Años Viejos
    if re.search(r"(31\s*(de\s*)?dic|treinta\s*y\s*uno\s*de\s*diciembre|a[ñn]o\s*viejo|viuda)", msg):
        ev = CARNAVAL_EVENTS["dec_31"]
        return ChatResponse(
            reply=(
                "¡Pura picardía y sátira pastusa, veci! El 31 de diciembre se celebra el Desfile de Años Viejos y viudas, "
                "despidiendo el año con monigotes que parodian la política y la cotidianidad al compás de ingeniosos testamentos. "
                "El recorrido arranca en la Senda Champagnat / Parque Bolívar."
            ),
            map_action=MapAction(
                action_type="ROUTE_TO_EVENT_START",
                target_name=f"Salida Años Viejos ({ev['start_location']})",
                target_coords=ev["start_coords"],
                event_date=ev["event_date"],
                category=ev["category"]
            )
        )

    # 8. Comida típica / Cuy / Gastronomía / 7 de Enero
    if re.search(r"(cuy|empanada|comida|almuerzo|gastronom[ií]a|hambre|restaurante|7\s*(de\s*)?ene|siete\s*de\s*enero|obonuco|catambuco)", msg):
        cuy_poi = EXTRA_POIS_KNOWLEDGE["comida_asadero_cuyquer"]
        return ChatResponse(
            reply=(
                "¡A comer sabroso, veci! En San Juan de Pasto no se puede perder el tradicional cuy asado al carbón con papas pastusas y ají de maní, "
                "o unas crocantes empanadas de añejo con pipián en la Plaza de Nariño. El 7 de enero la fiesta gastronómica culmina en el Festival del Cuy en Obonuco y Catambuco. "
                "Le sugiero los asaderos tradicionales en Mijitayo y los corregimientos."
            ),
            map_action=MapAction(
                action_type="FILTER_POIS",
                target_name=cuy_poi["name"],
                target_coords=cuy_poi["coords"],
                event_date="jan_07",
                category="comida"
            )
        )

    # 9. Salud / Primeros Auxilios / Médico / Ambulancia / Emergencia
    if re.search(r"(salud|m[eé]dico|primeros\s*auxilios|ambulancia|cruz\s*roja|defensa\s*civil|herido|desmayo|emergencia)", msg):
        pmu = EXTRA_POIS_KNOWLEDGE["salud_pmu_carnaval"]
        return ChatResponse(
            reply=(
                "¡Tranquilo, veci! Si presenta alguna emergencia o malestar de salud, contamos con Puestos de Mando Unificado (PMU) con médicos, "
                "paramédicos de la Cruz Roja, Defensa Civil y ambulancias listas. El PMU principal se encuentra en la Plaza del Carnaval y otro en la Senda Champagnat."
            ),
            map_action=MapAction(
                action_type="FILTER_POIS",
                target_name=pmu["name"],
                target_coords=pmu["coords"],
                category="salud"
            )
        )

    # 10. Baños / Servicios Sanitarios
    if re.search(r"(ba[ñn]o|servicio\s*sanitario|sanitario|orinar|pip[ií])", msg):
        bano = EXTRA_POIS_KNOWLEDGE["bano_plaza_carnaval"]
        return ChatResponse(
            reply=(
                "¡A la orden, veci! Para su comodidad se han dispuesto baterías de baños públicos portátiles y desinfectados "
                "en las zonas de mayor concentración de la Senda, especialmente en la Plaza del Carnaval, la Plaza de Nariño y el sector Champagnat."
            ),
            map_action=MapAction(
                action_type="FILTER_POIS",
                target_name=bano["name"],
                target_coords=bano["coords"],
                category="bano"
            )
        )

    # 11. Dónde empieza el desfile / Punto de salida / Senda
    if re.search(r"(d[oó]nde\s*(empieza|arranca|inicia|sale)|punto\s*de\s*(salida|partida)|senda)", msg):
        return ChatResponse(
            reply=(
                "¡Qué viva la Senda, veci! La mayoría de los grandes desfiles del Carnaval de Negros y Blancos "
                "(Años Viejos, Canto a la Tierra, Familia Castañeda y Desfile Magno) inician en la Senda Champagnat, "
                "ubicada en el sector sur de Pasto, avanzando por la Carrera 27 hacia el norte."
            ),
            map_action=MapAction(
                action_type="SHOW_SENDA",
                target_name="Punto de Salida Oficial (Senda Champagnat / Sur)",
                target_coords=[1.2052, -77.2796],
                category="desfile"
            )
        )

    # 12. Saludo o consulta general
    return ChatResponse(
        reply=(
            "¡Qué viva Pasto, carajo, veci! Soy GuaneñaBot, su asistente cultural oficial del Carnaval de Negros y Blancos. "
            "Puedo indicarle dónde inician los desfiles (ej. el 4 o 6 de enero), dónde saborear el mejor cuy tradicional, "
            "o cómo ubicar puestos de primeros auxilios y baños a lo largo de la Senda. ¿En qué le colaboro hoy?"
        ),
        map_action=MapAction(
            action_type="INFO_ONLY",
            target_name="San Juan de Pasto",
            target_coords=[1.2136, -77.2811],
            category="turismo"
        )
    )


def process_guanena_chat(request: ChatRequest) -> ChatResponse:
    """Envía la consulta del usuario a Gemini con fallback determinista resiliente ante fallos."""
    # 1. Intentar procesamiento con Google Gemini si la API key está disponible
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ["", "tu_clave_de_gemini_aqui"]:
        try:
            loc_context = ""
            if request.user_lat is not None and request.user_lng is not None:
                loc_context = f"\nUbicación actual del usuario: Latitud {request.user_lat}, Longitud {request.user_lng}."

            user_prompt = f"""CONSULTA DEL TURISTA/CIUDADANO:
"{request.message}"
{loc_context}
"""
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            model_name = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash")
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=GUANENA_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=ChatResponse,
                        temperature=0.3,
                    )
                )
            except Exception as primary_err:
                logger.warning(f"Aviso con {model_name} ({primary_err}). Reintentando con gemini-3.1-flash-lite...")
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=GUANENA_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=ChatResponse,
                        temperature=0.3,
                    )
                )

            if response and response.text:
                parsed = _parse_gemini_json_response(response.text)
                action_data = parsed.get("map_action")
                map_action = MapAction(**action_data) if action_data else None
                return ChatResponse(
                    reply=parsed.get("reply", "¡Qué viva Pasto, carajo!"),
                    map_action=map_action
                )
        except Exception as exc:
            logger.warning(
                f"[GUANEÑA_BOT] Aviso en conexión con Gemini API ({type(exc).__name__}: {exc}). "
                "Activando parser determinista de respaldo cultural."
            )

    # 2. Despacho resiliente mediante el parser determinista por reglas
    return deterministic_guanena_fallback(request.message)
