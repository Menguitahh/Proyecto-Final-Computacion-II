# FitBot – Modo TCP

FitBot es un entrenador personal impulsado por IA que funciona únicamente sobre sockets TCP.  
No hay frontend web: el proyecto incluye un servidor `asyncio` y un cliente CLI con registro/login, modo invitado y salida coloreada para distinguir mensajes de usuario y bot.

---

## 1. Prerrequisitos
- Python 3.9 o superior
- Redis en ejecución (local o remoto)
- Cuenta Groq para obtener `AI_API_KEY`
- Dependencias listadas en `requirements.txt`

---

## 2. Instalación
```bash
python -m venv .venv
source .venv/bin/activate      # En Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

Opcional: creá un `.env` y definí tus variables; si no, exportalas en la terminal:
```bash
export AI_API_KEY="tu_clave_groq"
# export REDIS_URL="redis://localhost:6379/0"
# export AI_MODEL="llama-3.1-8b-instant"
```

Levantá Redis:
```bash
redis-server
# o docker run -it --rm -p 6379:6379 redis:alpine
```

---

## 3. Ejecución

### Servidor TCP
```bash
python -m fitbot.tcp.server --host 0.0.0.0 --port 9000
```
Parámetros disponibles:
- `--workers N`: lanza N procesos en paralelo (`SO_REUSEPORT` cuando está disponible).
- `--host`, `--port`: cambian la interfaz y el puerto de escucha.

### Cliente CLI
```bash
python -m fitbot.tcp.client 127.0.0.1 9000
```

Menú inicial del cliente:
- `[1]` Registrarse (`/register usuario clave`) y persistir historial.
- `[2]` Iniciar sesión (`/login usuario clave`) para recuperar las últimas interacciones.
- `[3]` Continuar como invitado (`/guest`) sin guardar nada.
- `[q]` Salir.

Comandos dentro del chat:
- `/clear` borra el historial (persistido o temporal).
- `/quit` o `/exit` cierra la sesión.

Los mensajes usan códigos ANSI para mostrar al usuario en color celeste y al bot en magenta.  
Si tu terminal no soporta colores, ejecutá el cliente con `--no-auto` y escribí los comandos manualmente.

---

## 4. Componentes principales
- `fitbot/tcp/server.py`: servidor `asyncio`, autenticación básica, historial y soporte multiproceso.
- `fitbot/tcp/client.py`: cliente de consola con menú interactivo y handshake automático.
- `fitbot/chat_store.py`: capa de persistencia en Redis para usuarios, historiales y `/clear`.
- `fitbot/chatbot.py`: integración con Groq/OpenAI para respuestas en streaming.
- `fitbot/tcp/ansi.py`: paleta de colores compartida entre servidor y cliente.

Todo el código web y de pruebas frontend fue eliminado; el repositorio se centra exclusivamente en la solución TCP.
