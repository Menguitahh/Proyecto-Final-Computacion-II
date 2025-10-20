import logging
import re
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from fitbot import chat_store
from fitbot import chatbot as chatbot_logic

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
WELCOME_MESSAGE = "¡Hola! Soy FitBot, tu entrenador personal con IA. ¿En qué te puedo ayudar hoy?"
MESSAGE_LIMIT = 4000
MAX_HISTORY = 20
_CLIENT_ID_RE = re.compile(r"^[a-z0-9_-]{1,64}$")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await chat_store.init_db()
        logging.info("Base de datos inicializada")
    except Exception as exc:  # pragma: no cover - solo se ejecuta ante fallo en arranque
        logging.exception("No se pudo inicializar la DB de chats: %s", exc)
    try:
        yield
    finally:
        with suppress(Exception):
            await chat_store.close()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        csp = "; ".join(
            [
                "default-src 'self'",
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'",
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'",
                "img-src 'self' data: https:",
                "media-src 'self'",
                "connect-src 'self' ws: wss: https:",
            ]
        )
        response.headers.setdefault("Content-Security-Policy", csp)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


app.add_middleware(SecurityHeadersMiddleware)


class ConnectionManager:
    def __init__(self) -> None:
        self._histories: Dict[WebSocket, List[Dict[str, str]]] = {}
        self._client_ids: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self._client_ids[websocket] = client_id
        self._histories[websocket] = []

    def disconnect(self, websocket: WebSocket) -> None:
        self._histories.pop(websocket, None)
        self._client_ids.pop(websocket, None)

    def set_history(self, websocket: WebSocket, messages: List[Dict[str, str]]) -> None:
        self._histories[websocket] = list(messages)

    def history(self, websocket: WebSocket) -> List[Dict[str, str]]:
        return self._histories.setdefault(websocket, [])

    def trim_history(self, websocket: WebSocket, limit: int = MAX_HISTORY) -> None:
        history = self._histories.get(websocket)
        if history is not None and len(history) > limit:
            self._histories[websocket] = history[-limit:]

    async def send_json(self, websocket: WebSocket, payload: Dict) -> None:
        await websocket.send_json(payload)


manager = ConnectionManager()


def _is_valid_client_id(client_id: str) -> bool:
    return bool(_CLIENT_ID_RE.match(client_id))


def _build_prompt(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"role": "system", "content": chatbot_logic.SYSTEM_PROMPT}] + list(history)


async def _stream_assistant_reply(
    websocket: WebSocket,
    client_id: str,
    prompt_messages: List[Dict[str, str]],
) -> None:
    fallback = "No pude generar respuesta ahora. Intentá nuevamente."
    chunks: List[str] = []
    try:
        async for delta in chatbot_logic.astream_chat_completion(prompt_messages):
            if not delta:
                continue
            chunks.append(delta)
            await manager.send_json(websocket, {"type": "stream", "delta": delta})
    except Exception as exc:  # pragma: no cover - solo ante fallos del LLM
        logging.error("Error generando respuesta para %s: %s", client_id, exc)
        final_text = fallback
    else:
        final_text = "".join(chunks).strip() or fallback

    history = manager.history(websocket)
    history.append({"role": "assistant", "content": final_text})
    manager.trim_history(websocket)

    try:
        await chat_store.append_message(client_id, "assistant", final_text)
    except Exception as exc:
        logging.error("No se pudo guardar la respuesta para %s: %s", client_id, exc)

    try:
        await manager.send_json(websocket, {"type": "stream_end", "content": final_text})
    except Exception:
        pass


@app.get("/", response_class=HTMLResponse)
async def get_index() -> HTMLResponse:
    index_path = STATIC_DIR / "index.html"
    try:
        with open(index_path, encoding="utf-8") as fh:
            return HTMLResponse(content=fh.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse("<h1>FitBot</h1><p>Archivo index.html no encontrado.</p>", status_code=500)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "lm_client_available": chatbot_logic.is_client_available()})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    if not _is_valid_client_id(client_id):
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, client_id)
    logging.info("Nuevo cliente conectado: %s", client_id)

    await chat_store.upsert_session(client_id)
    stored_history = await chat_store.get_history(client_id, limit=50)
    if stored_history:
        manager.set_history(websocket, stored_history)
        await manager.send_json(websocket, {"type": "history", "messages": stored_history})

    await manager.send_json(
        websocket,
        {"type": "message", "role": "assistant", "content": WELCOME_MESSAGE},
    )

    try:
        while True:
            user_message = (await websocket.receive_text()).strip()
            if not user_message:
                continue

            if len(user_message) > MESSAGE_LIMIT:
                await manager.send_json(
                    websocket,
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": "Tu mensaje es muy largo. Por favor resumilo (máx. 4000 caracteres).",
                    },
                )
                continue

            if user_message.startswith("/log "):
                entry = user_message[5:].strip()
                if entry:
                    await chat_store.log_workout(client_id, entry)
                    await manager.send_json(
                        websocket,
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": f"Registro guardado: {entry}",
                        },
                    )
                else:
                    await manager.send_json(
                        websocket,
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": "Uso: /log <actividad>\nEjemplo: /log pushups 3x10",
                        },
                    )
                continue

            if user_message.startswith("/history"):
                workouts = await chat_store.get_workouts(client_id, limit=10)
                if not workouts:
                    msg = "No tenés registros aún. Usá /log para agregar."
                else:
                    lines = ["Últimos registros:"] + [f"- {w['created_at']}: {w['entry']}" for w in workouts]
                    msg = "\n".join(lines)
                await manager.send_json(
                    websocket, {"type": "message", "role": "assistant", "content": msg}
                )
                continue

            if user_message.startswith("/reset"):
                await chat_store.clear_history(client_id)
                manager.set_history(websocket, [])
                await manager.send_json(
                    websocket, {"type": "message", "role": "assistant", "content": "Conversación borrada."}
                )
                await manager.send_json(
                    websocket,
                    {"type": "message", "role": "assistant", "content": WELCOME_MESSAGE},
                )
                continue

            history = manager.history(websocket)
            history.append({"role": "user", "content": user_message})
            manager.trim_history(websocket)
            try:
                await chat_store.append_message(client_id, "user", user_message)
            except Exception as exc:
                logging.error("No se pudo guardar el mensaje del usuario %s: %s", client_id, exc)

            prompt_messages = _build_prompt(history)
            await _stream_assistant_reply(websocket, client_id, prompt_messages)

    except WebSocketDisconnect:
        logging.info("Cliente %s desconectado.", client_id)
    except Exception as exc:  # pragma: no cover - ruta de error inesperada
        logging.exception("Error en la sesión del cliente %s: %s", client_id, exc)
        with suppress(Exception):
            await manager.send_json(
                websocket,
                {
                    "type": "message",
                    "role": "assistant",
                    "content": "Uff, algo salió mal. Intentá recargar la página.",
                },
            )
    finally:
        manager.disconnect(websocket)
