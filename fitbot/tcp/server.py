import asyncio
import hashlib
import logging
import multiprocessing as mp
import secrets
import socket
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fitbot import chat_store
from fitbot import chatbot
from fitbot.tcp import ansi

WELCOME = (
    f"{ansi.COLOR_BOT}{ansi.BOLD}¡Hola! Soy FitBot (modo TCP){ansi.RESET}\n"
    f"{ansi.COLOR_INFO}Contame en qué puedo ayudarte. Recordá: "
    f"{ansi.COLOR_USER}/clear{ansi.RESET}{ansi.COLOR_INFO} borra el historial guardado y "
    f"{ansi.COLOR_USER}/quit{ansi.RESET}{ansi.COLOR_INFO} termina la sesión.{ansi.RESET}"
)
FALLBACK = f"{ansi.COLOR_ERROR}No pude generar respuesta ahora. Intentá nuevamente.{ansi.RESET}"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _build_client_id() -> str:
    token = secrets.token_hex(6)
    return f"tcp-{token}"


def _compose_messages(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"role": "system", "content": chatbot.SYSTEM_PROMPT}] + history


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@dataclass
class SessionContext:
    client_id: Optional[str] = None
    username: Optional[str] = None
    persist_history: bool = False
    active: bool = False
    history: List[Dict[str, str]] = field(default_factory=list)

    def reset_history(self) -> None:
        self.history.clear()

    def remember(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        self.history[:] = self.history[-20:]


def _format_dialog(header: str, continuation: str, text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return f"{header}:"
    formatted = [f"{header}: {lines[0]}"]
    formatted.extend(f"{continuation} {line}" if line else continuation for line in lines[1:])
    return "\n".join(formatted)


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


async def _send_history(send_line, entries: List[Dict[str, str]]) -> None:
    if not entries:
        await send_line(f"{ansi.COLOR_INFO}No había mensajes guardados. Empecemos un nuevo chat.{ansi.RESET}")
        return
    await send_line("")
    await send_line(f"{ansi.INFO_TAG} Últimos mensajes guardados{ansi.RESET}")
    for entry in entries:
        role = entry.get("role")
        content = entry.get("content", "")
        if role == "user":
            await send_line(_format_dialog(ansi.USER_TAG, ansi.USER_CONT, content))
        else:
            await send_line(_format_dialog(ansi.BOT_TAG, ansi.BOT_CONT, content))
    await send_line("")


async def _activate_guest(ctx: SessionContext, send_line) -> None:
    ctx.client_id = _build_client_id()
    ctx.username = None
    ctx.persist_history = False
    ctx.reset_history()
    ctx.active = True
    await send_line("")
    await send_line(f"{ansi.COLOR_SUCCESS}Modo invitado activado. Esta conversación no se guardará.{ansi.RESET}")
    await send_line(f"{ansi.COLOR_INFO}Ya podés empezar a chatear.{ansi.RESET}")


async def _register_user(username: str, password: str, ctx: SessionContext, send_line) -> None:
    client_id = await chat_store.register_user(username, _hash_password(password))
    ctx.client_id = client_id
    ctx.username = username
    ctx.persist_history = True
    ctx.reset_history()
    ctx.active = True
    await send_line("")
    await send_line(f"{ansi.COLOR_SUCCESS}¡Bienvenido, {username}! Tu cuenta quedó creada.{ansi.RESET}")
    await send_line(
        f"{ansi.COLOR_INFO}Tus mensajes se guardarán. Usá {ansi.COLOR_USER}/clear{ansi.RESET}"
        f"{ansi.COLOR_INFO} para borrar el historial cuando quieras.{ansi.RESET}"
    )


async def _login_user(username: str, password: str, ctx: SessionContext, send_line) -> None:
    record = await chat_store.get_user(username)
    if not record:
        await send_line(f"{ansi.COLOR_WARN}Usuario inexistente. Registrate con /register.{ansi.RESET}")
        return

    expected_hash = record.get("password_hash", "")
    if not expected_hash or expected_hash != _hash_password(password):
        await send_line(f"{ansi.COLOR_WARN}Clave incorrecta. Intentá nuevamente.{ansi.RESET}")
        return

    client_id = record.get("client_id") or _build_client_id()
    ctx.client_id = client_id
    ctx.username = username
    ctx.persist_history = True
    try:
        await chat_store.upsert_session(client_id)
        ctx.history = await chat_store.get_history(client_id, limit=20)
    except Exception as exc:  
        logging.exception("Error restaurando historial de %s: %s", client_id, exc)
        ctx.reset_history()
    ctx.active = True
    await send_line("")
    await send_line(f"{ansi.COLOR_SUCCESS}¡Hola de nuevo, {username}! Historial restaurado.{ansi.RESET}")
    await _send_history(send_line, ctx.history)
    await send_line(
        f"{ansi.COLOR_INFO}Cuando quieras, usá {ansi.COLOR_USER}/clear{ansi.RESET}{ansi.COLOR_INFO} para vaciar el historial o "
        f"{ansi.COLOR_USER}/quit{ansi.RESET}{ansi.COLOR_INFO} para salir.{ansi.RESET}"
    )


async def _handle_auth_command(message: str, ctx: SessionContext, send_line) -> None:
    lowered = message.lower()

    if lowered == "/guest":
        await _activate_guest(ctx, send_line)
        return

    if lowered.startswith("/register"):
        parts = message.split()
        if len(parts) != 3:
            await send_line("")
            await send_line(f"{ansi.COLOR_WARN}Uso: /register <usuario> <clave>{ansi.RESET}")
            return
        _, user, password = parts
        try:
            await _register_user(user, password, ctx, send_line)
        except ValueError:
            await send_line("")
            await send_line(f"{ansi.COLOR_WARN}Ese usuario ya existe. Probá con otro nombre o logueate con /login.{ansi.RESET}")
        except Exception as exc:  
            logging.exception("Error registrando usuario %s: %s", user, exc)
            await send_line("")
            await send_line(f"{ansi.COLOR_ERROR}No pude registrar el usuario ahora. Intentá más tarde.{ansi.RESET}")
        return

    if lowered.startswith("/login"):
        parts = message.split()
        if len(parts) != 3:
            await send_line("")
            await send_line(f"{ansi.COLOR_WARN}Uso: /login <usuario> <clave>{ansi.RESET}")
            return
        _, user, password = parts
        try:
            await _login_user(user, password, ctx, send_line)
        except Exception as exc:  
            logging.exception("Error consultando usuario %s: %s", user, exc)
            await send_line("")
            await send_line(f"{ansi.COLOR_ERROR}No pude verificar tus datos. Probá de nuevo más tarde.{ansi.RESET}")
        return

    await send_line("")
    await send_line(
        f"{ansi.COLOR_WARN}Necesitás indicar si sos invitado (/guest) o iniciar sesión (/login) o registrarte (/register).{ansi.RESET}"
    )


async def _clear_history(ctx: SessionContext, send_line) -> None:
    ctx.reset_history()
    if ctx.persist_history and ctx.client_id:
        try:
            await chat_store.clear_history(ctx.client_id)
            await send_line(f"{ansi.COLOR_SUCCESS}Historial guardado eliminado.{ansi.RESET}")
        except Exception as exc:  
            logging.exception("Error limpiando historial de %s: %s", ctx.client_id, exc)
            await send_line(f"{ansi.COLOR_ERROR}No pude borrar el historial. Intentá más tarde.{ansi.RESET}")
    else:
        await send_line(f"{ansi.COLOR_INFO}Historial temporal reiniciado (modo invitado).{ansi.RESET}")


async def _persist_message(ctx: SessionContext, role: str, content: str) -> None:
    if ctx.persist_history and ctx.client_id:
        await chat_store.append_message(ctx.client_id, role, content)


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    addr = writer.get_extra_info("peername")
    logging.info("Cliente TCP conectado: %s", addr)

    session = SessionContext()

    async def send_line(text: str) -> None:
        writer.write((text + "\n").encode("utf-8", errors="replace"))
        await writer.drain()

    await send_line(WELCOME)
    await send_line("")

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            message = data.decode("utf-8", errors="replace").strip()
            if not message:
                continue

            lowered = message.lower()

            if not session.active:
                await _handle_auth_command(message, session, send_line)
                continue

            if lowered in {"/quit", "/exit"}:
                await send_line("")
                await send_line(_format_dialog(ansi.BOT_TAG, ansi.BOT_CONT, "¡Hasta la próxima! 💪"))
                break

            if lowered == "/clear":
                await send_line("")
                await _clear_history(session, send_line)
                continue

            await _persist_message(session, "user", message)
            session.remember("user", message)

            reply = await _generate_reply(session.history)
            await _persist_message(session, "assistant", reply)
            session.remember("assistant", reply)

            await send_line("")
            await send_line(_format_dialog(ansi.BOT_TAG, ansi.BOT_CONT, reply))
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


async def _serve(host: str, port: int, reuse_port: bool) -> None:
    if not chatbot.is_client_available():
        logging.warning("El proveedor de IA no está disponible. Asegurate de configurar AI_API_KEY.")

    await chat_store.init_db()
    effective_reuse = reuse_port
    try:
        server = await asyncio.start_server(handle_client, host=host, port=port, reuse_port=reuse_port)
    except (OSError, ValueError) as exc:
        if reuse_port:
            logging.warning("No se pudo habilitar reuse_port: %s. Reintento con reuse_port desactivado.", exc)
            server = await asyncio.start_server(handle_client, host=host, port=port, reuse_port=False)
            effective_reuse = False
        else:
            raise
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    logging.info("Servidor TCP FitBot escuchando en %s (reuse_port=%s)", addrs, effective_reuse)

    try:
        async with server:
            await server.serve_forever()
    finally:
        await chat_store.close()


def _worker_entry(host: str, port: int, reuse_port: bool) -> None:
    try:
        asyncio.run(_serve(host, port, reuse_port))
    except KeyboardInterrupt:
        pass


def _spawn_worker(ctx: mp.context.BaseContext, host: str, port: int, reuse_port: bool) -> mp.Process:
    proc = ctx.Process(target=_worker_entry, args=(host, port, reuse_port), daemon=False)
    proc.start()
    return proc


async def _run_single(host: str, port: int, reuse_port: bool) -> None:
    await _serve(host, port, reuse_port)


async def main() -> None:
    import argparse

    default_host = _detect_default_host()

    parser = argparse.ArgumentParser(description="Servidor TCP de FitBot")
    parser.add_argument("--host", default=default_host, help="Dirección donde escuchar (default: %(default)s)")
    parser.add_argument("--port", type=int, default=9000, help="Puerto TCP (default: 9000)")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Cantidad de workers paralelos (usa reuse_port para balancear, default: 1)",
    )
    args = parser.parse_args()

    workers = max(1, args.workers)
    reuse_port = workers > 1

    if workers == 1:
        await _run_single(args.host, args.port, reuse_port=False)
        return

    logging.info("Iniciando %s workers en %s:%s con reuse_port", workers, args.host, args.port)
    ctx = mp.get_context("spawn")
    procs = [_spawn_worker(ctx, args.host, args.port, reuse_port) for _ in range(workers)]

    try:
        for proc in procs:
            proc.join()
    except KeyboardInterrupt:
        logging.info("Recibido CTRL+C, finalizando workers…")
        for proc in procs:
            proc.terminate()
    finally:
        for proc in procs:
            if proc.is_alive():
                proc.join()


if __name__ == "__main__":  
    asyncio.run(main())
