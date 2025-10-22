```markdown
# Informe de Diseño: FitBot

## Arquitectura General
La aplicación sigue una arquitectura **Cliente-Servidor** sencilla. FastAPI expone una API WebSocket (`fitbot/app.py`) que sirve la SPA del chat (`static/`). Para el requisito académico también se incluye un servidor TCP puro (`fitbot/tcp/server.py`) que utiliza sockets crudos; ambos modos comparten la misma lógica de negocio y almacenamiento.

## Modelo de Concurrencia
Todo el servidor corre sobre `asyncio`. Cada mensaje del usuario desencadena una tarea asíncrona que consume la API de Groq en modo streaming. Mientras llegan los tokens del modelo, se van reenviando al WebSocket del cliente; otros usuarios no quedan bloqueados.

## Modelo de Inteligencia Artificial
Se utiliza **Llama 3.1 (llama-3.1-8b-instant)** hospedado por Groq a través de su API compatible con OpenAI.

**Justificación:**
1. **Costo:** Groq ofrece un plan gratuito con cuota generosa para proyectos personales/educativos.
2. **Latencia baja:** La infraestructura LPU entrega tokens rápidamente, ofreciendo una experiencia comparable o mejor a un despliegue local sin requerir GPU.
3. **Simplicidad:** Configurar la API reduce la complejidad de instalación y facilita despliegues en la nube o en equipos modestos.

## Gestión de Estado
Cada WebSocket mantiene una lista circular con las últimas 20 interacciones para alimentar al modelo y evitar el crecido de memoria. Las conversaciones completas se almacenan en Redis (`fitbot/chat_store.py`) y se recuperan cuando el usuario vuelve a conectarse. El streaming finaliza guardando la respuesta y notificando al cliente con un evento `stream_end`.
```
