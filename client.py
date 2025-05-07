import asyncio

async def tcp_client():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    try:
        while True:
            message = input("Mensaje al servidor: ")
            if message.lower() == 'salir':
                break

            writer.write(message.encode())
            await writer.drain()

            data = await reader.read(100)
            print(f"Respuesta del servidor: {data.decode()}")
    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(tcp_client())
