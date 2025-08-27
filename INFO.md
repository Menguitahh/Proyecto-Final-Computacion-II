```markdown
# Informe de Diseño: FitBot

## Arquitectura General
Se optó por una arquitectura **Cliente-Servidor**. Esta decisión permite desacoplar la interfaz de usuario (`client.py`) de la lógica principal y la conexión con la IA (`server.py`). Esto facilita el mantenimiento y permite que múltiples usuarios accedan al servicio de forma concurrente, manteniendo sesiones de chat individuales y aisladas.

## Modelo de Concurrencia: `asyncio`
Para gestionar las conexiones simultáneas de múltiples clientes, se utiliza la librería `asyncio` de Python. Un servidor de chatbot es una aplicación inherentemente limitada por I/O (espera de red y de la respuesta de la IA). `asyncio` es ideal para este escenario, ya que maneja miles de conexiones con un solo hilo de manera eficiente y con un bajo consumo de recursos, a diferencia de modelos más pesados como `multithreading` o `multiprocessing`.

## Modelo de Inteligencia Artificial: Llama 3 Local
La decisión clave del proyecto fue utilizar un **modelo de lenguaje grande (LLM) de código abierto (Llama 3) ejecutándose localmente** a través de LM Studio, en lugar de depender de APIs de pago como OpenAI o Google.

**Justificación:**
1.  **Privacidad:** Los datos de fitness y salud son sensibles. Al procesar todo localmente, se garantiza que ninguna conversación privada del usuario se envía a servidores de terceros.
2.  **Costo:** Elimina por completo los costos operativos por uso de API, haciendo la aplicación verdaderamente gratuita después de la configuración inicial.
3.  **Control y Disponibilidad:** No depende de la disponibilidad de un servicio externo ni de sus posibles límites de cuota.

## Gestión de Estado
Cada cliente conectado tiene una sesión independiente en el servidor. El estado de la conversación (el historial de mensajes) se almacena en un diccionario en la memoria del servidor, asociado al `writer` de cada cliente. Esto permite que el chatbot tenga contexto sobre la conversación actual para dar respuestas coherentes y personalizadas.