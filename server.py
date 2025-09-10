import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import chatbot_logic
import chat_store
from typing import List, Dict

# 1. Configuración de la aplicación FastAPI
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI()

# Monta la carpeta 'static' para que el navegador pueda acceder a index.html, css y js
app.mount("/static", StaticFiles(directory="static"), name="static")

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

# 2. Endpoint para servir la página principal del chat (index.html)
@app.get("/", response_class=HTMLResponse)
async def get():
    try:
        with open("static/index.html", encoding="utf-8") as f:
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
    await manager.connect(websocket, client_id)
    logging.info(f"Nuevo cliente conectado: %s", client_id)
    # Asegura que la sesión exista en DB y carga historial
    await chat_store.upsert_session(client_id)
    history = await chat_store.get_history(client_id, limit=50)
    manager.active_connections[websocket] = history.copy()
    # Enviar historial al cliente para rehidratación
    if history:
        await manager.send_json({"type": "history", "messages": history}, websocket)
    
    # Mensaje de bienvenida inicial
    welcome_message = "¡Hola! Soy FitBot, tu entrenador personal con IA. ¿En qué te puedo ayudar hoy?"
    await manager.send_json({"type": "message", "role": "assistant", "content": welcome_message}, websocket)

    try:
        while True:
            # Espera a recibir un mensaje del cliente
            user_message = await websocket.receive_text()

            # Validación básica de entrada para evitar mensajes excesivos
            if len(user_message) > 4000:
                await manager.send_message(
                    "FitBot: Tu mensaje es muy largo. Por favor resumilo (máx. 4000 caracteres).",
                    websocket,
                )
                continue
            
            # Obtiene el historial de esta conexión específica
            current_history = manager.active_connections[websocket]
            current_history.append({"role": "user", "content": user_message})
            # Persistir mensaje del usuario
            await chat_store.append_message(client_id, "user", user_message)

            # Llama a la lógica del chatbot
            # Llama la IA en un hilo para no bloquear el event loop
            ai_response = await asyncio.to_thread(
                chatbot_logic.get_ai_trainer_response, current_history
            )

            # Actualiza el historial
            current_history.append({"role": "assistant", "content": ai_response})
            # Limita el historial para no exceder la memoria
            manager.active_connections[websocket] = current_history[-20:]
            # Persistir respuesta de la IA
            await chat_store.append_message(client_id, "assistant", ai_response)

            # Envía la respuesta de FitBot de vuelta al cliente (JSON)
            await manager.send_json({"type": "message", "role": "assistant", "content": ai_response}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info("Cliente %s desconectado.", client_id)
    except Exception as e:
        logging.exception("Error en la sesión del cliente %s: %s", client_id, e)
        await manager.send_json({"type": "message", "role": "assistant", "content": "Uff, algo salió mal. Intenta recargar la página."}, websocket)
        manager.disconnect(websocket)

# Para ejecutar el servidor, usarás uvicorn desde la terminal
# comando: uvicorn server:app --reload


@app.on_event("startup")
async def on_startup():
    try:
        await chat_store.init_db()
        logging.info("Base de datos de chats inicializada")
    except Exception as e:
        logging.exception("No se pudo inicializar la DB de chats: %s", e)
