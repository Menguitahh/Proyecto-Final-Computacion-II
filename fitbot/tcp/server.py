import asyncio
import logging
import secrets
import socket
from contextlib import suppress
from typing import Dict, List

from fitbot import chat_store
from fitbot import chatbot

WELCOME = "¡Hola! Soy FitBot (modo TCP). Escribí tus dudas de entrenamiento o usá /quit para salir."
FALLBACK = "No pude generar respuesta ahora. Intentá nuevamente."

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _build_client_id() -> str:
    token = secrets.token_hex(6)
    return f"tcp-{token}"


def _compose_messages(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"role": "system", "content": chatbot.SYSTEM_PROMPT}] + history


async def _generate_reply(history: List[Dict[str, str]]) -> str:
    prompt = _compose_messages(history)
    fragments: List[str] = []
    try:
        async for delta in chatbot.astream_chat_completion(prompt):
            if delta:
                fragments.append(delta)
    except Exception as exc:  
        logging.error("Error generando respuesta en modo TCP: %s", exc)
        return FALLBACK
    text = "".join(fragments).strip()
    return text or FALLBACK


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    addr = writer.get_extra_info("peername")
    logging.info("Cliente TCP conectado: %s", addr)

    client_id = _build_client_id()
    history: List[Dict[str, str]] = []

    await chat_store.upsert_session(client_id)
    prev = await chat_store.get_history(client_id, limit=20)
    history.extend(prev)

    async def send_line(text: str) -> None:
        writer.write((text + "\n").encode("utf-8", errors="replace"))
        await writer.drain()

    await send_line(WELCOME)

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            message = data.decode("utf-8", errors="replace").strip()
            if not message:
                continue

            if message.lower() in {"/quit", "/exit"}:
                await send_line("FitBot: ¡Hasta la próxima! 💪")
                break

            await chat_store.append_message(client_id, "user", message)
            history.append({"role": "user", "content": message})
            history[:] = history[-20:]

            reply = await _generate_reply(history)
            await chat_store.append_message(client_id, "assistant", reply)
            history.append({"role": "assistant", "content": reply})
            history[:] = history[-20:]

            await send_line(f"FitBot: {reply}")
    except asyncio.CancelledError:
        pass
    except Exception as exc:  
        logging.exception("Error atendiendo a %s: %s", addr, exc)
        with suppress(Exception):
            await send_line("FitBot: Ocurrió un error inesperado. Intentalo más tarde.")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        logging.info("Cliente TCP desconectado: %s", addr)


def _detect_default_host() -> str:
    """Return a host IP suitable for external clients, falling back to all interfaces."""
    try:
        hostname_ip = socket.gethostbyname(socket.gethostname())
        if hostname_ip and not hostname_ip.startswith("127."):
            return hostname_ip
    except Exception as exc:
        logging.debug("Fallo al resolver hostname local: %s", exc)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            ip = probe.getsockname()[0]
        if ip and not ip.startswith("127."):
            return ip
    except Exception as exc:
        logging.debug("Fallo al detectar la IP local: %s", exc)

    logging.warning("No se pudo detectar IP local no loopback, usando 0.0.0.0")
    return "0.0.0.0"


async def main() -> None:
    import argparse

    default_host = _detect_default_host()

    parser = argparse.ArgumentParser(description="Servidor TCP de FitBot")
    parser.add_argument("--host", default=default_host, help="Dirección donde escuchar (default: %(default)s)")
    parser.add_argument("--port", type=int, default=9000, help="Puerto TCP (default: 9000)")
    args = parser.parse_args()

    if not chatbot.is_client_available():
        logging.warning("El proveedor de IA no está disponible. Asegurate de configurar AI_API_KEY.")

    await chat_store.init_db()
    server = await asyncio.start_server(handle_client, host=args.host, port=args.port)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    logging.info("Servidor TCP FitBot escuchando en %s", addrs)

    try:
        async with server:
            await server.serve_forever()
    finally:
        await chat_store.close()


if __name__ == "__main__":  
    asyncio.run(main())
