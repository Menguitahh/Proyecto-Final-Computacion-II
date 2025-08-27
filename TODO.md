# Mejoras y Futuras Características (TODO)

Esta es una lista de posibles mejoras para futuras versiones del sistema de chat.

## Core

* [ ] **Nombres de usuario**: Permitir que los usuarios elijan un apodo al conectarse en lugar de ser identificados por su IP y puerto.
* [ ] **Salas de chat**: Implementar la capacidad de crear y unirse a diferentes salas o canales temáticos.
* [ ] **Mensajes privados**: Añadir un comando `/msg <usuario> <mensaje>` para enviar mensajes directos.
* [ ] **Persistencia de mensajes**: Guardar el historial de chat en un archivo de texto o una base de datos simple (SQLite).

## Chatbot

* [ ] **Respuestas más inteligentes**: Integrar una librería simple de NLP (Natural Language Processing) para que el bot pueda entender preguntas básicas.
* [ ] **API externa**: Conectar el bot a una API externa para obtener datos en tiempo real (ej. `/clima <ciudad>`).
* [ ] **Juegos simples**: Implementar juegos por texto como Adivina el Número.

## Robustez y Seguridad

* [ ] **Manejo de errores mejorado**: Añadir un manejo más robusto para desconexiones inesperadas y datos malformados.
* [ ] **Cifrado**: Implementar SSL/TLS para cifrar la comunicación entre cliente y servidor.
* [ ] **Autenticación**: Añadir un sistema simple de registro y login de usuarios.