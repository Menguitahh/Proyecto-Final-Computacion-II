# Mejoras y Futuras Características de FitBot

## Funcionalidades Principales
- [ ] **Persistencia de Perfil:** Guardar el perfil del usuario (metas, experiencia, etc.) en un archivo (`.json`, `.db`) para que el bot lo recuerde entre sesiones.
- [ ] **Registro de Entrenamientos:** Implementar un comando para que los usuarios puedan registrar sus entrenamientos (ej: `/log pushups 3x10`). El bot guardaría este progreso.
- [ ] **Generación de Gráficos:** Crear visualizaciones simples del progreso del usuario (ej: un gráfico de texto del peso levantado a lo largo del tiempo).
- [ ] **Programación de Recordatorios:** Permitir al usuario configurar recordatorios para sus días de entrenamiento.

## Mejoras del Chatbot
- [ ] **Ajuste Fino del Modelo (Fine-Tuning):** Re-entrenar un modelo de IA de código abierto con datos específicos de fitness para que se especialice aún más como entrenador personal.
- [ ] **Modo "Drill Sergeant":** Añadir un modo de personalidad alternativo para el bot, más estricto y exigente, que el usuario pueda activar.
- [ ] **Integración con APIs de Nutrición:** Conectar el bot a una API de alimentos para obtener información calórica o de macronutrientes de comidas específicas.

## Mejoras de la Aplicación
- [ ] **Interfaz Gráfica de Usuario (GUI):** Migrar de la consola a una interfaz gráfica de escritorio (usando Tkinter, PyQt) o a una aplicación web (usando Flask, FastAPI).
- [ ] **Autenticación de Usuarios:** Añadir un sistema de login con contraseña para proteger los perfiles de usuario guardados.
- [ ] **Contenedorización con Docker:** Empaquetar la aplicación y sus dependencias en un contenedor de Docker para facilitar aún más el despliegue.