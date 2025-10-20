# Guía de Instalación de FitBot

Sigue estos pasos para configurar y lanzar la aplicación completa.

## 1. Prerrequisitos
- Python 3.9 o superior
- Git
- Cuenta gratuita en Groq para obtener una API key (<https://console.groq.com/keys>)

## 2. Clonar el repositorio
```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <NOMBRE_DEL_DIRECTORIO>
```

## 3. Crear entorno y dependencias
```bash
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

## 4. Levantar Redis
- Opción rápida: `docker compose up redis -d`
- Alternativa: instala Redis en tu sistema y asegurate de que `REDIS_URL` apunte a esa instancia.

## 5. Configuración del proveedor
1) Duplica `.env.example` en `.env`.
2) Completa `AI_API_KEY` con la clave de Groq.
3) (Opcional) Ajusta `AI_MODEL` si querés usar otro modelo; por defecto `llama-3.1-8b-instant` ofrece buen equilibrio entre calidad y cuota gratuita.

## 6. Ejecutar el servidor web
```bash
uvicorn fitbot.app:app --reload
```
Luego abre tu navegador en:
```
http://127.0.0.1:8000/
```

## 7. (Opcional) Servidor TCP sin web
Para probar la interacción por sockets crudos:

```bash
python -m fitbot.tcp.server --host 127.0.0.1 --port 9000
# En otra terminal
python -m fitbot.tcp.client 127.0.0.1 9000
```

## 8. Solución de problemas
- "AI_API_KEY no está configurada": crea el archivo `.env` o exporta la variable en tu entorno de shell.
- "401 Unauthorized" en los logs: revisa que la API key de Groq sea válida y tenga cuota disponible.
- Error de WebSocket/Re-conexión: revisa que `uvicorn` siga activo y que no haya firewalls bloqueando `ws://`.
- Archivos pesados: los videos de fondo pueden no estar versionados; puedes añadir los tuyos en `static/` o usar un fondo estático.
