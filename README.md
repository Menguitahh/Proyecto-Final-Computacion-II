# FitBot (modo TCP puro)

Este repositorio contiene únicamente la versión por sockets TCP de FitBot, un entrenador personal impulsado por IA.  
El flujo es todo en terminal: un servidor asyncio que acepta múltiples clientes concurrently, y un cliente CLI con soporte para registro/login, invitado y colores ANSI.

## Dependencias

- Python 3.9+
- Redis en ejecución (local o remoto)
- Cuenta en [Groq](https://console.groq.com/keys) para obtener `AI_API_KEY`
- Paquetes Python: ver `requirements.txt`

### Instalación rápida

```bash
python -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

Configura tus credenciales en el entorno (opcionalmente usando `.env`):

```bash
export AI_API_KEY="tu_clave_de_groq"
# Opcional:
# export AI_MODEL="llama-3.1-8b-instant"
# export REDIS_URL="redis://localhost:6379/0"
```

Asegurate de que Redis esté disponible. Por ejemplo:

```bash
redis-server             # instalación local
# o, si preferís contenedor:
# docker run -it --rm -p 6379:6379 redis:alpine
```

## Uso

Lanza el servidor TCP (usa 9000 por defecto y autodetecta la IP local):

```bash
python -m fitbot.tcp.server --host 0.0.0.0 --port 9000
```

En otra terminal iniciá el cliente oficial:

```bash
python -m fitbot.tcp.client 127.0.0.1 9000
```

El cliente muestra un pequeño menú:

- `[1]` Registrarse (`/register usuario contraseña`) y persistir historial.
- `[2]` Iniciar sesión (`/login usuario contraseña`) y restaurar las últimas 20 interacciones.
- `[3]` Modo invitado (`/guest`) sin guardar nada.
- `[q]` Salir.

Comandos dentro del chat:

- `/clear` borra el historial guardado (o reinicia la sesión temporal si sos invitado).
- `/quit` o `/exit` cierran la conexión.

La salida usa ANSI para diferenciar mensajes del usuario y del bot.  
Si tu terminal no soporta colores, ejecutá el cliente con `--no-auto` y enviá los comandos manualmente.

## Arquitectura resumida

- `fitbot/tcp/server.py`: servidor asyncio con workers multi-proceso opcionales (`--workers` usa `SO_REUSEPORT` cuando está disponible).
- `fitbot/tcp/client.py`: cliente CLI con autenticación básica y sesión automática.
- `fitbot/chat_store.py`: persistencia en Redis para usuarios e historiales.
- `fitbot/chatbot.py`: wrapper del SDK de Groq/OpenAI para generar respuestas en streaming.
- `fitbot/tcp/ansi.py`: constantes ANSI compartidas.

Todo lo relacionado con UI web, FastAPI o pruebas de front-end fue eliminado para dejar un proyecto enfocado 100 % en sockets TCP.
