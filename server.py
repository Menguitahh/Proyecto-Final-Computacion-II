import asyncio
import chatbot_logic

clients = {}

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Nueva sesión de cliente iniciada desde: {addr}")
    nickname = None
    try:
        data = await reader.readuntil(b'\n')
        nickname = data.decode().strip()

        clients[writer] = {"name": nickname, "addr": addr, "history": []}

        writer.write(f"¡Hola {nickname}! Soy FitBot, tu entrenador personal con IA.\n".encode())
        writer.write(f"Estoy listo para conversar. Para salir, escribe '/quit'.\n".encode())
        await writer.drain()
        
        print(f"Cliente '{nickname}' desde {addr} ha iniciado su sesión.")

        while True:
            data = await reader.read(1024)
            if not data:
                break

            user_message = data.decode().strip()
            if not user_message or user_message.lower() == '/quit':
                break

            current_history = clients[writer]["history"]
            current_history.append({"role": "user", "content": user_message})

            ai_response = chatbot_logic.get_ai_trainer_response(current_history)

            current_history.append({"role": "assistant", "content": ai_response})
            clients[writer]["history"] = current_history[-20:]

            writer.write(f"FitBot: {ai_response}\n".encode())
            await writer.drain()

    except (ConnectionResetError, asyncio.IncompleteReadError) as e:
        print(f"Error en la sesión del cliente {nickname or addr}: {e}")
    finally:
        if writer in clients:
            print(f"Cerrando sesión del cliente '{clients[writer]['name']}' desde {addr}")
            del clients[writer]
        else:
            print(f"Cerrando sesión de cliente no identificado desde {addr}")

        if not writer.is_closing():
            writer.close()
            await writer.wait_closed()

async def main():
    server_host = '127.0.0.1'
    server_port = 8888
    server = await asyncio.start_server(handle_client, server_host, server_port)
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Servidor escuchando en {addrs}...')
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCerrando el servidor.")