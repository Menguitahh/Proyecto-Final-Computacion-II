```markdown
# Informe de Diseño: FitBot (TCP)

## Arquitectura General
El sistema quedó reducido a un único modo de operación: un servidor TCP asíncrono (`fitbot/tcp/server.py`) y un cliente de consola (`fitbot/tcp/client.py`). Ambos se comunican mediante sockets crudos sobre `asyncio`. Las credenciales del usuario y el historial se guardan en Redis para permitir reconexiones desde distintas terminales o máquinas.

## Modelo de Concurrencia
El servidor usa `asyncio.start_server` y puede escalar horizontalmente con múltiples workers (`--workers N`) compartiendo el mismo puerto gracias a `SO_REUSEPORT`. Cada conexión mantiene un `SessionContext` con las últimas 20 interacciones para alimentar al modelo sin crecer indefinidamente.

## Modelo de Inteligencia Artificial
Se conserva el uso de **Llama 3** hospedado en Groq vía su API compatible con OpenAI. La clase `fitbot/chatbot.py` se encarga de:
- Resolver el mejor modelo disponible entre una lista preferida.
- Crear clientes síncronos/asíncronos reutilizables.
- Emitir respuestas en streaming (`astream_chat_completion`) para mantener una experiencia fluida.

## Gestión de Estado
`fitbot/chat_store.py` abstrae el acceso a Redis:
- Registro/login de usuarios (hash SHA-256 sobre la contraseña).
- Persistencia de historiales por `client_id`.
- Utilidades para limpiar historial (`/clear`) y mantener la lista circular.

Los invitados reciben IDs efímeros y nunca se persisten en Redis.

## Interfaz de Usuario
Todo ocurre en consola. El cliente CLI ofrece un menú inicial y colorea las conversaciones con códigos ANSI definidos en `fitbot/tcp/ansi.py`, diferenciando claramente los mensajes del usuario y del bot.
```
