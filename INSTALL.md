# Guía de Instalación (modo TCP)

## Prerrequisitos
- Python 3.9 o superior
- Redis en ejecución (local o remoto)
- Cuenta en Groq para obtener `AI_API_KEY`

## Pasos
```bash
git clone <URL_DEL_REPO>
cd <NOMBRE_DEL_DIRECTORIO>

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

Configura las variables necesarias (podés usar `.env`):
```bash
export AI_API_KEY="tu_clave"
# export REDIS_URL="redis://localhost:6379/0"
# export AI_MODEL="llama-3.1-8b-instant"
```

Levantá Redis:
```bash
redis-server
# o docker run -it --rm -p 6379:6379 redis:alpine
```

Arrancá el servidor TCP:
```bash
python -m fitbot.tcp.server --host 0.0.0.0 --port 9000
```

En otra terminal iniciá el cliente CLI:
```bash
python -m fitbot.tcp.client 127.0.0.1 9000
```

El menú inicial permite registrarte, iniciar sesión o continuar como invitado.  
Dentro del chat podés usar `/clear` para borrar historial y `/quit` para salir.

## Solución de problemas
- **`AI_API_KEY` vacía:** exportá la variable o cargala desde `.env`.
- **Errores de conexión a Redis:** verificá `REDIS_URL` y que el servicio esté en marcha.
- **Sin colores en la terminal:** ejecutá el cliente con `--no-auto` y enviá los comandos manualmente.
