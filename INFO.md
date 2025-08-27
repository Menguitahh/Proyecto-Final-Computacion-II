# Informe de Diseño del Sistema de Chat

## 1. Modelo Cliente-Servidor

Se optó por una arquitectura cliente-servidor centralizada. Un único programa **servidor** actúa como punto central de comunicación, gestionando las conexiones y retransmitiendo los mensajes. Los **clientes** son programas ligeros que solo necesitan saber la dirección del servidor para conectarse.

**Justificación**: Este modelo es simple de implementar y gestionar. Centralizar la lógica en el servidor facilita la adición de nuevas características (como el chatbot, registro de mensajes, etc.) sin tener que modificar los clientes.

## 2. Protocolo de Comunicación: Sockets sobre TCP

La comunicación se basa en sockets TCP/IP.

**Justificación**: Se eligió **TCP** por su fiabilidad. A diferencia de UDP, TCP garantiza la entrega ordenada y sin errores de los paquetes de datos, lo cual es fundamental para una aplicación de chat donde el orden y la integridad de los mensajes son críticos.

## 3. Modelo de Concurrencia: I/O Asíncrona con `asyncio`

Para manejar múltiples clientes simultáneamente, se implementó un modelo de concurrencia basado en I/O asíncrona utilizando la librería `asyncio` de Python.

**Justificación**: Un servidor de chat es una aplicación eminentemente "I/O-bound" (limitada por la entrada/salida), ya que pasa la mayor parte de su tiempo esperando a que los clientes envíen datos por la red.

Se evaluaron las siguientes alternativas:

* **Multithreading**: Aunque es una opción viable, el Global Interpreter Lock (GIL) de Python limita el paralelismo real de los hilos. Además, la gestión de locks y la sincronización entre hilos puede añadir complejidad.
* **Multiprocessing (`fork`)**: Proporciona paralelismo real al eludir el GIL, pero cada proceso consume una cantidad significativa de memoria. Escalar a un gran número de clientes sería ineficiente.

**`asyncio` fue la elección final** porque maneja miles de conexiones concurrentes en un único hilo con un consumo de recursos mínimo. Utiliza un bucle de eventos para gestionar las operaciones de red de forma no bloqueante, lo cual es la solución más eficiente y escalable para este tipo de problema.

## 4. Estructura del Código

El código se separó en `server.py` y `client.py` para mantener una clara separación de responsabilidades, facilitando el mantenimiento y la depuración.