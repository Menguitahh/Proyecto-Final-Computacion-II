import logging
import os
import time
from contextlib import suppress
from typing import AsyncIterator, Dict, Iterable, List, Optional, Sequence

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

load_dotenv()

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.1-8b-instant"

AI_BASE_URL = os.getenv("AI_BASE_URL") or os.getenv("LM_BASE_URL", DEFAULT_BASE_URL)
AI_API_KEY = os.getenv("AI_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("LM_API_KEY")
AI_MODEL = os.getenv("AI_MODEL") or os.getenv("LM_MODEL", DEFAULT_MODEL)
PREFERRED_MODELS = [
    AI_MODEL,
    "llama-3.2-3b-preview",
    "llama-3.1-8b-instant",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE") or os.getenv("LM_TEMPERATURE", "0.7"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS") or os.getenv("LM_MAX_TOKENS", "1500"))
AI_CLIENT_TIMEOUT = float(os.getenv("AI_CLIENT_TIMEOUT") or os.getenv("LM_CLIENT_TIMEOUT", "120.0"))
CLIENT_CHECK_TTL = float(os.getenv("AI_CLIENT_CHECK_TTL") or os.getenv("LM_CLIENT_CHECK_TTL", "10.0"))

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
""".strip()


def _build_sync_client() -> OpenAI:
    return OpenAI(
        base_url=AI_BASE_URL,
        api_key=AI_API_KEY,
        timeout=AI_CLIENT_TIMEOUT,
    )


def _build_async_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=AI_BASE_URL,
        api_key=AI_API_KEY,
        timeout=AI_CLIENT_TIMEOUT,
    )


_last_check_ts: float = 0.0
_last_check_ok: bool = False
_resolved_model: Optional[str] = None


def _extract_model_ids(items: Iterable) -> List[str]:
    ids: List[str] = []
    for item in items:
        identifier = getattr(item, "id", None)
        if identifier:
            ids.append(str(identifier))
            continue
        if isinstance(item, dict) and item.get("id"):
            ids.append(str(item["id"]))
    return ids


def _list_available_models() -> Sequence[str]:
    client = _build_sync_client()
    try:
        response = client.models.list()
    finally:
        with suppress(Exception):
            client.close()
    data = getattr(response, "data", response)
    if isinstance(data, Sequence):
        return _extract_model_ids(data)
    return _extract_model_ids(list(data))


def _resolve_model() -> str:
    global _resolved_model
    if _resolved_model:
        return _resolved_model

    seen = set()
    candidates: List[str] = []
    for name in PREFERRED_MODELS:
        if not name or name in seen:
            continue
        candidates.append(name)
        seen.add(name)
    available = set(_list_available_models())
    for candidate in candidates:
        if candidate in available:
            if AI_MODEL and candidate != AI_MODEL:
                logging.warning(
                    "Modelo preferido %s no disponible, usando %s", AI_MODEL, candidate
                )
            _resolved_model = candidate
            return candidate

    if available:
        fallback = sorted(available)[0]
        logging.warning(
            "Ninguno de los modelos preferidos está disponible; usando %s", fallback
        )
        _resolved_model = fallback
        return fallback

    raise RuntimeError("Groq no publicó modelos disponibles para esta API key")


def is_client_available() -> bool:
    """Devuelve True si el proveedor remoto de IA estuvo disponible recientemente."""
    global _last_check_ts, _last_check_ok
    now = time.monotonic()
    if now - _last_check_ts <= CLIENT_CHECK_TTL:
        return _last_check_ok

    if not AI_API_KEY:
        logging.debug("AI_API_KEY no configurada; el proveedor remoto queda deshabilitado")
        _last_check_ok = False
        _last_check_ts = now
        return False

    try:
        _resolve_model()
        _last_check_ok = True
    except Exception as exc: 
        logging.debug("No se pudo conectar al cliente local de IA: %s", exc)
        _last_check_ok = False
    _last_check_ts = now
    return _last_check_ok


async def astream_chat_completion(messages: List[Dict[str, str]]) -> AsyncIterator[str]:
    """Itera fragmentos de texto del modelo de manera asíncrona."""
    if not AI_API_KEY:
        raise RuntimeError(
            "AI_API_KEY no está configurada. Registrate en Groq (gratuito) y exporta AI_API_KEY o GROQ_API_KEY."
        )
    client: Optional[AsyncOpenAI] = None
    stream = None
    try:
        client = _build_async_client()
        model_name = _resolve_model()
        stream = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
            stream=True,
        )
        async for chunk in stream:
            with suppress(Exception):
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta
    except Exception as exc:
        logging.exception("Error durante el stream de respuesta del LLM: %s", exc)
        raise
    finally:
        if client:
            with suppress(Exception):
                await client.close()
