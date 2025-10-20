# FitBot: Tu Entrenador Personal con IA

**FitBot** es un chatbot con interfaz web diseñado para actuar como un entrenador personal. Utiliza un modelo Llama 3 hospedado en Groq (plan gratuito) a través de la API compatible con OpenAI para ofrecer respuestas rápidas sobre fitness, rutinas y nutrición.

La aplicación usa FastAPI con WebSocket para sostener múltiples conversaciones simultáneas sin bloquear a otros usuarios, incluso cuando cada uno recibe respuestas en streaming. El estado (usuarios, historial de chat y registros de entrenamiento) se persiste en Redis, lo que simplifica la ejecución en contenedores o despliegues en la nube.

## Características
- Conversaciones con IA: dialoga en lenguaje natural sobre tus metas de fitness.
- Gratis (hasta el límite del plan de Groq) y sin necesidad de hardware especializado.
- Respuestas en streaming con baja latencia gracias a la infraestructura LPU de Groq.
- Multi-cliente: múltiples usuarios pueden conectarse y tener sesiones privadas en paralelo.
- Persistencia en Redis: historial y registros se conservan entre sesiones sin depender de SQLite locales.

## Uso básico
1. Crea una cuenta gratuita en [Groq](https://console.groq.com/keys) y copia tu clave de API.
2. Duplica `.env.example` en `.env`, completá `AI_API_KEY` y dejá `AI_MODEL=llama-3.1-8b-instant` (modelo estable sugerido en el plan gratuito de Groq).
3. Levantá Redis (por ejemplo `docker compose up redis -d` o instala Redis localmente y actualiza `REDIS_URL`).
4. Instala dependencias y ejecuta `uvicorn fitbot.app:app --reload`.
5. Abre `http://127.0.0.1:8000/` para empezar a chatear con FitBot.

Nota: podés seguir usando `uvicorn server:app --reload` por compatibilidad.

## Ejecutar todo con Docker Compose

```bash
docker compose up --build
```

Esto levanta dos contenedores: Redis (con almacenamiento persistente en `redis-data/`) y la aplicación web en `http://localhost:8000`. Asegurate de exportar `AI_API_KEY` antes de ejecutar el comando si querés pasar la clave sin escribirla en `.env`.

## Modo TCP (sockets sin Web)

Para cumplir con el requisito de sockets “raw” podés interactuar con FitBot vía terminal:

```bash
# Servidor TCP (puerto por defecto 9000)
python -m fitbot.tcp.server --host 127.0.0.1 --port 9000

# Cliente mínimo incluido
python -m fitbot.tcp.client 127.0.0.1 9000

# También podés usar netcat
nc 127.0.0.1 9000
```

Cada conexión TCP genera un `client_id` propio, guarda el historial en Redis y usa el mismo modelo Groq que la versión web. Comandos disponibles en el cliente: `/quit` o `/exit` para cortar la sesión.
