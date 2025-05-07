import asyncio

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Cliente conectado: {addr}")

    while True:
        data = await reader.read(100)
        if not data:
            break  # El cliente cerró la conexión

        message = data.decode()
        print(f"Recibido de {addr}: {message}")

        response = f"Servidor recibió: {message}"
        writer.write(response.encode())
        await writer.drain()

    print(f"Cliente desconectado: {addr}")
    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    print("Servidor escuchando en 127.0.0.1:8888")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
