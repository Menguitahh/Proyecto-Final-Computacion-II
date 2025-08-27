import asyncio
import sys

async def receive_messages(reader):
    while True:
        try:
            data = await reader.read(1024)
            if not data:
                print("\nDesconexión del servidor. Presiona Enter para salir.")
                break
            print(f"\r{data.decode().strip()}\nTú: ", end="")
        except (ConnectionResetError, asyncio.CancelledError):
            print("\nConexión con el servidor perdida. Presiona Enter para salir.")
            break

async def send_messages(writer):
    loop = asyncio.get_event_loop()
    while True:
        try:
            message = await loop.run_in_executor(None, sys.stdin.readline)
            writer.write(message.encode())
            await writer.drain()
            if message.strip().lower() == '/quit':
                print("Desconectando...")
                break
        except (asyncio.CancelledError, KeyboardInterrupt):
            break

async def main():
    server_host = '127.0.0.1'
    server_port = 8888
    try:
        reader, writer = await asyncio.open_connection(server_host, server_port)
    except ConnectionRefusedError:
        print(f"Error: No se pudo conectar al servidor. ¿Está corriendo?")
        return

    nickname = input("Por favor, introduce tu nombre para la sesión: ")
    writer.write(f"{nickname}\n".encode())
    await writer.drain()
    
    receive_task = asyncio.create_task(receive_messages(reader))
    send_task = asyncio.create_task(send_messages(writer))

    print("--- Conectado a FitBot. Escribe '/quit' para salir. ---")
    print("Tú: ", end="")

    done, pending = await asyncio.wait(
        [receive_task, send_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()
    
    if not writer.is_closing():
        writer.close()
        await writer.wait_closed()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCliente cerrado.")