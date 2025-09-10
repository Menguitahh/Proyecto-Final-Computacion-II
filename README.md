# FitBot: Tu Entrenador Personal con IA

**FitBot** es un chatbot con interfaz web diseñado para actuar como un entrenador personal. Utiliza un modelo de lenguaje grande (Llama 3) que se ejecuta localmente en tu computadora para ofrecer conversaciones privadas, personalizadas y sin costo sobre fitness, rutinas y nutrición.

La aplicación utiliza una arquitectura cliente-servidor (FastAPI + WebSocket) que permite que múltiples usuarios mantengan conversaciones simultáneas e independientes con el bot.

Además, el proyecto incluye un servidor TCP asíncrono opcional para cumplir con el requisito académico de usar sockets TCP crudos y manejar concurrencia con `asyncio`.

## Características
- **Conversaciones con IA:** Dialoga en lenguaje natural sobre tus metas de fitness.
- **Privacidad Total:** El modelo de IA corre en tu máquina local. Tus datos de salud nunca salen de tu computadora.
- **Gratis y Sin Límites:** Al ser un modelo local, no hay costos por uso ni cuotas de API.
- **Multi-Cliente:** Múltiples usuarios pueden conectarse y tener sus propias sesiones privadas al mismo tiempo.

## Uso Básico
1.  Asegurate de que el servidor de IA local (LM Studio) esté corriendo y que el modelo esté cargado (ver `INSTALL.md`).
2.  Inicia la API con `uvicorn server:app --reload`.
3.  Abre `http://127.0.0.1:8000/` en tu navegador.
4.  ¡Empezá a chatear con FitBot! Hacé preguntas sobre rutinas, ejercicios o nutrición.

Nota: el antiguo cliente de consola fue retirado en favor de la interfaz web.

## Modo TCP (Sockets)
Para ejecutar el servidor TCP puro (sin WebSocket) y probar concurrencia con `asyncio`:

```bash
python tcp_server.py [HOST] [PUERTO]
# Ejemplo
python tcp_server.py 127.0.0.1 9000
```

Podés conectarte con `nc` (netcat) o usando el cliente incluido:

```bash
# Con netcat
nc 127.0.0.1 9000

# Con el cliente del repo
python tcp_client.py 127.0.0.1 9000
```

Cada conexión mantiene su propio historial en el servidor. El servidor limita el tamaño de los mensajes y recorta el historial para evitar uso excesivo de memoria.
