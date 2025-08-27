# FitBot: Tu Entrenador Personal con IA

**FitBot** es un chatbot de consola diseñado para actuar como un entrenador personal. Utiliza un modelo de lenguaje grande (Llama 3) que se ejecuta localmente en tu computadora para ofrecer conversaciones privadas, personalizadas y sin costo sobre fitness, rutinas y nutrición.

La aplicación utiliza una arquitectura cliente-servidor que permite que múltiples usuarios mantengan conversaciones simultáneas e independientes con el bot.

## Características
- **Conversaciones con IA:** Dialoga en lenguaje natural sobre tus metas de fitness.
- **Privacidad Total:** El modelo de IA corre en tu máquina local. Tus datos de salud nunca salen de tu computadora.
- **Gratis y Sin Límites:** Al ser un modelo local, no hay costos por uso ni cuotas de API.
- **Multi-Cliente:** Múltiples usuarios pueden conectarse y tener sus propias sesiones privadas al mismo tiempo.

## Uso Básico
1.  Asegurate de que el servidor de IA local (LM Studio) y el `server.py` estén corriendo (ver `INSTALL.md`).
2.  Ejecutá el cliente con `python3 client.py`.
3.  Introducí un nombre para tu sesión.
4.  ¡Empezá a chatear con FitBot! Hacé preguntas sobre rutinas, ejercicios o nutrición.
5.  Para terminar la sesión, escribí `/quit`.