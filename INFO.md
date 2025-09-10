```markdown
# Informe de Diseño: FitBot

## Arquitectura General
Se optó por una arquitectura **Cliente-Servidor**. La aplicación principal expone una interfaz web (FastAPI + WebSocket en `server.py`). Además, se incluye un servidor **TCP puro** (`tcp_server.py`) para cumplir con requisitos académicos de manejo de sockets con `asyncio`. En ambos casos, múltiples usuarios pueden acceder de forma concurrente, manteniendo sesiones de chat independientes.

## Modelo de Concurrencia: `asyncio`
Para gestionar las conexiones simultáneas de múltiples clientes, se utiliza la librería `asyncio` de Python. Un servidor de chatbot es inherentemente I/O-bound (red y respuesta del LLM). `asyncio` es ideal para este escenario, manejando muchas conexiones en un solo hilo de manera eficiente. Las llamadas bloqueantes al LLM se derivan a un pool de hilos usando `asyncio.to_thread` para no bloquear el event loop.

## Modelo de Inteligencia Artificial: Llama 3 Local
La decisión clave del proyecto fue utilizar un **modelo de lenguaje grande (LLM) de código abierto (Llama 3) ejecutándose localmente** a través de LM Studio, en lugar de depender de APIs de pago como OpenAI o Google.

**Justificación:**
1.  **Privacidad:** Los datos de fitness y salud son sensibles. Al procesar todo localmente, se garantiza que ninguna conversación privada del usuario se envía a servidores de terceros.
2.  **Costo:** Elimina por completo los costos operativos por uso de API, haciendo la aplicación verdaderamente gratuita después de la configuración inicial.
3.  **Control y Disponibilidad:** No depende de la disponibilidad de un servicio externo ni de sus posibles límites de cuota.

## Gestión de Estado
Cada cliente conectado mantiene una sesión independiente. El estado de la conversación (historial de mensajes) se guarda en memoria asociado al WebSocket (en `server.py`) o a la conexión TCP (en `tcp_server.py`). El historial se recorta a las últimas 20 intervenciones para limitar el consumo de memoria.
