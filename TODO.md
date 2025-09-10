# Mejoras y Futuras Características de FitBot

## Funcionalidades Principales
- [ ] Persistencia de perfil: guardar el perfil del usuario (metas, experiencia, etc.) en un archivo (`.json`, `.db`) para que el bot lo recuerde entre sesiones.
- [ ] Registro de entrenamientos: implementar un comando para que los usuarios puedan registrar sus entrenamientos (ej: `/log pushups 3x10`). El bot guardaría este progreso.
- [ ] Generación de gráficos: crear visualizaciones simples del progreso del usuario (ej: un gráfico del peso levantado a lo largo del tiempo).
- [ ] Programación de recordatorios: permitir al usuario configurar recordatorios para sus días de entrenamiento.

## Mejoras del Chatbot
- [ ] Ajuste fino del modelo (fine-tuning): re-entrenar un modelo de IA de código abierto con datos específicos de fitness para que se especialice aún más como entrenador personal.
- [ ] Modo "Drill Sergeant": añadir un modo de personalidad alternativo para el bot, más estricto y exigente, que el usuario pueda activar.
- [ ] Integración con APIs de nutrición: conectar el bot a una API de alimentos para obtener información calórica o de macronutrientes de comidas específicas.

## Mejoras de la Aplicación
- [ ] Interfaz Gráfica de Usuario (GUI): mantener la app web (FastAPI) y considerar app de escritorio (Tkinter/PyQt) si se requiere offline completo.
- [ ] Autenticación de usuarios: añadir un sistema de login con contraseña para proteger los perfiles de usuario guardados.
- [ ] Contenedorización con Docker: empaquetar la aplicación y sus dependencias en un contenedor de Docker para facilitar aún más el despliegue.

