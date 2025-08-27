import asyncio
import chatbot_logic

clients = {}

def get_name(writer):
    return clients.get(writer, {}).get("name", "Desconocido")

def broadcast(message: str, sender_writer):
    sender_name = get_name(sender_writer)
    print(f"Transmitiendo desde {sender_name}: {message.strip()}")
    for writer in clients:
        if writer != sender_writer:
            try:
                writer.write(message.encode())
                asyncio.create_task(writer.drain())
            except ConnectionError:
                pass

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Conexión entrante de {addr}")
    nickname = None
    try:
        data = await reader.readuntil(b'\n')
        nickname = data.decode().strip()

        clients[writer] = {"name": nickname, "addr": addr, "history": []}

        writer.write(f"¡Bienvenido, {nickname}!\n".encode())
        await writer.drain()
        
        print(f"El cliente {addr} se ha identificado como '{nickname}'")
        broadcast(f"SYSTEM: ¡{nickname} se ha unido al chat!\n", writer)

        while True:
            data = await reader.read(1024)
            if not data:
                break

            user_message = data.decode().strip()
            if not user_message or user_message.lower() == '/quit':
                continue

            current_history = clients[writer]["history"]
            current_history.append({"role": "user", "content": user_message})

            ai_response = chatbot_logic.get_ai_trainer_response(current_history)

            current_history.append({"role": "assistant", "content": ai_response})
            clients[writer]["history"] = current_history[-20:]

            writer.write(f"FitBot: {ai_response}\n".encode())
            await writer.drain()

    except (ConnectionResetError, asyncio.IncompleteReadError, ConnectionAbortedError) as e:
        print(f"Error con el cliente {nickname or addr}: {e}")
    finally:
        sender_name = get_name(writer)
        if writer in clients:
            del clients[writer]
        
        if sender_name != "Desconocido":
            broadcast(f"SYSTEM: {sender_name} ha abandonado el chat.\n", writer)
        
        if not writer.is_closing():
            writer.close()
            await writer.wait_closed()
        print(f"Conexión con {sender_name or addr} cerrada.")

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