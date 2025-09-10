import asyncio
import sys
import logging
from typing import Dict, List

from fitbot import chatbot as chatbot_logic


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class ChatSession:
    def __init__(self) -> None:
        self.history: List[Dict[str, str]] = []

    async def handle_message(self, text: str) -> str:
        self.history.append({"role": "user", "content": text})
        # Call blocking LLM in a worker thread to keep the loop responsive
        reply: str = await asyncio.to_thread(
            chatbot_logic.get_ai_trainer_response, self.history
        )
        self.history.append({"role": "assistant", "content": reply})
        # Keep only recent turns to bound memory
        self.history = self.history[-20:]
        return reply


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    addr = writer.get_extra_info("peername")
    logging.info("TCP cliente conectado: %s", addr)
    session = ChatSession()

    async def send_line(line: str) -> None:
        writer.write((line + "\n").encode("utf-8", errors="ignore"))
        await writer.drain()

    # Welcome banner
    await send_line("FitBot: ¡Hola! Soy tu entrenador personal con IA. Escribí tus preguntas.")
    await send_line("FitBot: Comandos: /quit para salir.")

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            msg = data.decode("utf-8", errors="ignore").strip()
            if not msg:
                continue

            if msg.lower() in {"/quit", "/exit"}:
                await send_line("FitBot: ¡Hasta la próxima! 💪")
                break

            if len(msg) > 4000:
                await send_line("FitBot: Tu mensaje es muy largo. Resumilo por favor (máx. 4000).")
                continue

            # Get assistant reply
            try:
                reply = await session.handle_message(msg)
            except Exception as e:  # Defensive: avoid killing server on one client failure
                logging.exception("Error procesando mensaje de %s: %s", addr, e)
                reply = "Uff, algo salió mal procesando tu mensaje. Intentá nuevamente."

            # TCP client (consola) no renderiza Markdown; mantenemos tal cual para compatibilidad
            # El cliente puede mostrarlo como texto o interpretarlo aparte si quiere.
            await send_line(f"FitBot: {reply}")

    except asyncio.CancelledError:
        # Graceful shutdown path
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        logging.info("TCP cliente desconectado: %s", addr)


async def main() -> None:
    # Basic CLI args without external deps (satisfies sys usage)
    host = "127.0.0.1"
    port = 9000

    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("Puerto inválido, usando 9000", file=sys.stderr)

    if not chatbot_logic.is_client_available():
        logging.warning("El cliente LLM no está disponible. ¿Iniciaste LM Studio?")

    server = await asyncio.start_server(handle_client, host=host, port=port)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    logging.info("Servidor TCP FitBot escuchando en %s", addrs)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApagando servidor TCP...")
