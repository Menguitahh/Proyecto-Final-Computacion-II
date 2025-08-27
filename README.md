# Proyecto Final Computacion II
# README: Chatbot de Consola en Python

Bienvenido al Chatbot de Consola. Este es un sistema de chat cliente-servidor multiusuario desarrollado en Python utilizando `asyncio` para la concurrencia.

## Uso Básico

1.  **Inicia el servidor** como se describe en `INSTALL.md`.
2.  **Inicia uno o más clientes** en terminales separadas.
3.  Escribe tu mensaje en la terminal del cliente y presiona Enter. Tu mensaje será enviado a todos los demás participantes del chat.

## Comandos Disponibles

El chatbot responde a los siguientes comandos especiales:

* `/quit`: Desconecta al cliente del servidor de forma segura.
* `/help`: Muestra una lista de comandos disponibles. (Debes implementar esta lógica en `server.py`).
* `/time`: Muestra la hora actual del servidor. (Debes implementar esta lógica).

## Diagrama de Arquitectura Simplificado

[Cliente 1] <--> [Servidor] <--> [Cliente 2]
               |
           [Chatbot]