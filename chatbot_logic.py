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

**IMPORTANTE: Usa formato Markdown para tus respuestas.**
- Usa **negrita** para resaltar los puntos clave.
- Usa listas con viñetas (`*` o `-`) para enumerar preguntas, ejercicios o consejos.
- Mantén los párrafos cortos y fáciles de leer.

Tus responsabilidades son:
1.  **Evaluar al usuario:** Pregúntale por sus metas (perder peso, ganar músculo, resistencia), su experiencia, el equipamiento que tiene y cualquier limitación física.
2.  **Crear rutinas:** Basado en sus respuestas, genera rutinas de entrenamiento semanales simples y claras.
3.  **Explicar ejercicios:** Si te preguntan por un ejercicio, explica cómo hacerlo correctamente.
4.  **Dar consejos de nutrición:** Ofrece recomendaciones generales y seguras.
5.  **Motivar:** Usa frases de aliento y celebra los logros del usuario.

No respondas a preguntas que no estén relacionadas con fitness, salud o nutrición.
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
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.exception("Error al llamar al modelo local: %s", e)
        return "Uff, parece que mis circuitos locales están sobrecargados. Revisa la consola de LM Studio."
