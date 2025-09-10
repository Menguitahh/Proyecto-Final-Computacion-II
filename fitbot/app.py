import asyncio
import logging
import re
from threading import Thread
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fitbot import chatbot as chatbot_logic
from fitbot import chat_store
from typing import List, Dict

# 1. ConfiguraciÃ³n de la aplicaciÃ³n FastAPI
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await chat_store.init_db()
        logging.info("Base de datos de chats inicializada")
    except Exception as e:
        logging.exception("No se pudo inicializar la DB de chats: %s", e)
    yield

app = FastAPI(lifespan=lifespan)

# Monta la carpeta 'static' para que el navegador pueda acceder a index.html, css y js
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Seguridad bÃ¡sica con encabezados HTTP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        csp = "; ".join([
            "default-src 'self'",
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'",
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'",
            "img-src 'self' data: https:",
            "media-src 'self'",
            "connect-src 'self' ws: wss: https:",
        ])
        response.headers.setdefault("Content-Security-Policy", csp)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Clase para gestionar las conexiones de los clientes
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, List[Dict]] = {}
        self.ws_client_ids: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.ws_client_ids[websocket] = client_id
        self.active_connections[websocket] = []  # historial en memoria

    def disconnect(self, websocket: WebSocket):
        # Elimina de forma segura evitando KeyError
        self.active_connections.pop(websocket, None)
        self.ws_client_ids.pop(websocket, None)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_json(self, payload: Dict, websocket: WebSocket):
        await websocket.send_json(payload)

manager = ConnectionManager()

_CLIENT_ID_RE = re.compile(r"^[a-z0-9_-]{1,64}$")

def _is_valid_client_id(client_id: str) -> bool:
    return bool(_CLIENT_ID_RE.match(client_id))

# 2. Endpoint para servir la pÃ¡gina principal del chat (index.html)
@app.get("/", response_class=HTMLResponse)
async def get():
    try:
        index_path = STATIC_DIR / "index.html"
        with open(index_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>FitBot</h1><p>Archivo index.html no encontrado.</p>", status_code=500)

# Endpoint de salud simple
@app.get("/health")
async def health():
    return JSONResponse({
        "status": "ok",
        "lm_client_available": chatbot_logic.is_client_available()
    })

# 3. Endpoint del WebSocket para la comunicación en tiempo real

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # Validar client_id antes de aceptar
    if not _is_valid_client_id(client_id):
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, client_id)
    logging.info("Nuevo cliente conectado: %s", client_id)

    # Asegura sesión en DB y carga historial
    await chat_store.upsert_session(client_id)
    history = await chat_store.get_history(client_id, limit=50)
    manager.active_connections[websocket] = history.copy()
    if history:
        await manager.send_json({"type": "history", "messages": history}, websocket)

    # Mensaje de bienvenida (personalizado con perfil si existe)
    # Mensaje de bienvenida
    welcome_message = "¡Hola! Soy FitBot, tu entrenador personal con IA. ¿En qué te puedo ayudar hoy?"
    await manager.send_json({"type": "message", "role": "assistant", "content": welcome_message}, websocket)









    try:
        while True:
            user_message = (await websocket.receive_text()).strip()
            if not user_message:
                continue

            # Límite básico
            if len(user_message) > 4000:
                await manager.send_message("FitBot: Tu mensaje es muy largo. Por favor resumilo (máx. 4000 caracteres).", websocket)
                continue

            # Comandos
            if user_message.startswith("/log "):
                entry = user_message[5:].strip()
                if entry:
                    await chat_store.log_workout(client_id, entry)
                    await manager.send_json({"type": "message", "role": "assistant", "content": f"Registro guardado: {entry}"}, websocket)
                else:
                    await manager.send_json({"type": "message", "role": "assistant", "content": "Uso: /log <actividad>\nEjemplo: /log pushups 3x10"}, websocket)
                continue
            if user_message.startswith("/history"):
                workouts = await chat_store.get_workouts(client_id, limit=10)
                if not workouts:
                    await manager.send_json({"type": "message", "role": "assistant", "content": "No tenés registros aún. Usá /log para agregar."}, websocket)
                else:
                    lines = ["Últimos registros:"] + [f"- {w['created_at']}: {w['entry']}" for w in workouts]
                    await manager.send_json({"type": "message", "role": "assistant", "content": "\n".join(lines)}, websocket)
                continue
            if user_message.startswith("/reset"):
                await chat_store.clear_history(client_id)
                manager.active_connections[websocket] = []
                await manager.send_json({"type": "message", "role": "assistant", "content": "Conversación borrada."}, websocket)
                welcome_message = "¡Hola! Soy FitBot, tu entrenador personal con IA. ¿En qué te puedo ayudar hoy?"
                welcome_message = "¡Hola! Soy FitBot, tu entrenador personal con IA. ¿En qué te puedo ayudar hoy?"
                await manager.send_json({"type": "message", "role": "assistant", "content": welcome_message}, websocket)
            current_history = manager.active_connections[websocket]
            current_history.append({"role": "user", "content": user_message})
            await chat_store.append_message(client_id, "user", user_message)

            profile = await chat_store.get_profile(client_id)
            loop = asyncio.get_running_loop()
            full_parts: List[str] = []

            def send_delta(delta: str):
                try:
                    loop.call_soon_threadsafe(asyncio.create_task, manager.send_json({"type": "stream", "delta": delta}, websocket))
                except Exception:
                    pass

            def worker():
                try:
                    msgs = ([{"role": "system", "content": chatbot_logic.SYSTEM_PROMPT}] +
                            ([{"role": "system", "content": "Perfil del usuario\n" + "\n".join(
                                f"- {k.capitalize()}: {v}" for k, v in (profile or {}).items() if v)}] if profile else []) +
                            current_history)
                    stream = chatbot_logic.client.chat.completions.create(
                        model=chatbot_logic.LM_MODEL,
                        messages=msgs,
                        temperature=float(chatbot_logic.LM_TEMPERATURE),
                        max_tokens=int(chatbot_logic.LM_MAX_TOKENS),
                        stream=True,
                    )
                    for chunk in stream:
                        try:
                            delta = chunk.choices[0].delta.content or ""
                        except Exception:
                            delta = ""
                        if delta:
                            full_parts.append(delta)
                            send_delta(delta)
                except Exception:
                    pass

                final_text = "".join(full_parts).strip() or "No pude generar respuesta ahora. Intentánuevamente."

                async def finalize():
                    ch = manager.active_connections.get(websocket, [])
                    ch.append({"role": "assistant", "content": final_text})
                    manager.active_connections[websocket] = ch[-20:]
                    try:
                        await chat_store.append_message(client_id, "assistant", final_text)
                    except Exception:
                        pass
                    await manager.send_json({"type": "stream_end", "content": final_text}, websocket)

                loop.call_soon_threadsafe(asyncio.create_task, finalize())

            Thread(target=worker, daemon=True).start()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info("Cliente %s desconectado.", client_id)
    except Exception as e:
        logging.exception("Error en la sesión del cliente %s: %s", client_id, e)
        await manager.send_json({"type": "message", "role": "assistant", "content": "Uff, algo salió mal. Intentárecargar la página."}, websocket)
        manager.disconnect(websocket)

# Para ejecutar el servidor, usarás uvicorn desde la terminal
# comando: uvicorn server:app --reload












