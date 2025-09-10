import os
import logging
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# Carga variables desde .env si existe
load_dotenv()

LM_BASE_URL = os.getenv("LM_BASE_URL", "http://localhost:1234/v1")
LM_API_KEY = os.getenv("LM_API_KEY", "not-needed")
LM_MODEL = os.getenv("LM_MODEL", "Meta-Llama-3-8B-Instruct")
LM_TEMPERATURE = float(os.getenv("LM_TEMPERATURE", "0.7"))
LM_MAX_TOKENS = int(os.getenv("LM_MAX_TOKENS", "1500"))

try:
    client = OpenAI(base_url=LM_BASE_URL, api_key=LM_API_KEY)
except Exception as e:
    logging.error("Error al conectar con el servidor local de IA: %s", e)
    client = None

SYSTEM_PROMPT = """
Eres 'FitBot', un Entrenador Personal virtual. Tu tono es motivador, amigable y profesional.

IMPORTANTE: Usa formato Markdown.
- Usa **negrita** para resaltar.
- Usa listas con viñetas para pasos o consejos.
- Párrafos cortos y fáciles de leer.

Al responder:
1) Si ya conoces metas, experiencia, equipamiento o limitaciones del usuario (por su perfil o historial), NO vuelvas a preguntarlo. Úsalo directamente y solo pedí lo que falte o confirmá cambios.
2) Crea rutinas claras y semanales según su contexto.
3) Explica ejercicios cuando te lo pidan (técnica, respiración y seguridad).
4) Da consejos de nutrición generales y seguros.
5) Motiva y celebra el progreso.

No respondas a temas fuera de fitness, salud o nutrición.
"""


def is_client_available() -> bool:
    """Indica si el cliente de IA está disponible."""
    return client is not None


def get_ai_trainer_response(conversation_history: List[Dict]) -> str:
    if not client:
        return "No pude conectarme al motor de IA local. ¿Iniciaste el servidor en LM Studio?"

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

        response = client.chat.completions.create(
            model=LM_MODEL,
            messages=messages,
            temperature=LM_TEMPERATURE,
            max_tokens=LM_MAX_TOKENS
        )
        
        # Manejo defensivo de respuestas vacías o estructura inesperada
        try:
            content = response.choices[0].message.content
        except Exception:
            content = None
        if not content or not str(content).strip():
            return "Lo siento, no pude generar una respuesta ahora. Probá nuevamente o revisá LM Studio."
        return str(content).strip()

    except Exception as e:
        logging.exception("Error al llamar al modelo local: %s", e)
        return "Uff, parece que mis circuitos locales están sobrecargados. Revisa la consola de LM Studio."


