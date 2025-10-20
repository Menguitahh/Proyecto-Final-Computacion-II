```markdown
# Informe de Diseño: FitBot

## Arquitectura General
La aplicación sigue una arquitectura **Cliente-Servidor** sencilla. FastAPI expone una API WebSocket (`fitbot/app.py`) que sirve la SPA del chat (`static/`). Cada navegador abre un WebSocket y mantiene su sesión independiente: el historial de mensajes se guarda en memoria por conexión y se sincroniza en Redis para persistencia.

## Modelo de Concurrencia
Todo el servidor corre sobre `asyncio`. Cada mensaje del usuario desencadena una tarea asíncrona que consume la API de Groq en modo streaming. Mientras llegan los tokens del modelo, se van reenviando al WebSocket del cliente; otros usuarios no quedan bloqueados.

## Modelo de Inteligencia Artificial
Se utiliza **Llama 3.1 (llama-3.1-8b-instant)** hospedado por Groq a través de su API compatible con OpenAI. Esta elección reemplaza el antiguo flujo con LM Studio y elimina la necesidad de ejecutar modelos pesados en la computadora del usuario.

**Justificación:**
1. **Costo:** Groq ofrece un plan gratuito con cuota generosa para proyectos personales/educativos.
2. **Latencia baja:** La infraestructura LPU entrega tokens rápidamente, ofreciendo una experiencia comparable o mejor a un despliegue local sin requerir GPU.
3. **Simplicidad:** Configurar la API reduce la complejidad de instalación y facilita despliegues en la nube o en equipos modestos.

## Gestión de Estado
Cada WebSocket mantiene una lista circular con las últimas 20 interacciones para alimentar al modelo y evitar el crecido de memoria. Las conversaciones completas se almacenan en Redis (`fitbot/chat_store.py`) y se recuperan cuando el usuario vuelve a conectarse. El streaming finaliza guardando la respuesta y notificando al cliente con un evento `stream_end`.
```
