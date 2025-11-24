import argparse
import asyncio
import getpass
import sys
from typing import Optional

from fitbot.tcp import ansi

SUCCESS_MARKERS = [
    "modo invitado activado",
    "¡bienvenido",
    "¡hola de nuevo",
    "ya podés empezar a chatear",
    "historial restaurado",
]

FAILURE_MARKERS = [
    "uso: /register",
    "uso: /login",
    "ese usuario ya existe",
    "no pude registrar",
    "no pude verificar",
    "usuario inexistente",
    "clave incorrecta",
    "necesitás indicar",
]


def _prompt_initial_command() -> str:
    menu = (
        f"\n{ansi.COLOR_INFO}{ansi.BOLD}Elegí cómo querés iniciar:{ansi.RESET}\n"
        f"  {ansi.COLOR_SUCCESS}[1]{ansi.RESET} Registrarme (usuario nuevo)\n"
        f"  {ansi.COLOR_SUCCESS}[2]{ansi.RESET} Iniciar sesión\n"
        f"  {ansi.COLOR_SUCCESS}[3]{ansi.RESET} Continuar como invitado "
        f"{ansi.COLOR_WARN}(no se guarda historial){ansi.RESET}\n"
        f"  {ansi.COLOR_SUCCESS}[q]{ansi.RESET} Salir\n"
    )

    option_aliases = {
        "register": {"1", "r", "register", "registro"},
        "login": {"2", "l", "login"},
        "guest": {"3", "g", "guest", "invitado"},
        "quit": {"q", "quit", "exit", "salir"},
    }

    alias_lookup = {
        alias: option for option, aliases in option_aliases.items() for alias in aliases
    }

    def handle_register() -> Optional[str]:
        username = input(f"{ansi.COLOR_INFO}Usuario:{ansi.RESET} ").strip()
        if not username or " " in username:
            print(f"{ansi.COLOR_WARN}El usuario no puede estar vacío ni contener espacios.{ansi.RESET}")
            return None
        password = getpass.getpass(f"{ansi.COLOR_INFO}Clave:{ansi.RESET} ").strip()
        if not password or " " in password:
            print(f"{ansi.COLOR_WARN}La clave no puede estar vacía ni contener espacios.{ansi.RESET}")
            return None
        return f"/register {username} {password}"

    def handle_login() -> str:
        username = input(f"{ansi.COLOR_INFO}Usuario:{ansi.RESET} ").strip()
        password = getpass.getpass(f"{ansi.COLOR_INFO}Clave:{ansi.RESET} ").strip()
        return f"/login {username} {password}"

    def handle_guest() -> str:
        return "/guest"

    def handle_quit() -> None:
        print(f"{ansi.COLOR_INFO}Hasta la próxima.{ansi.RESET}")
        sys.exit(0)

    handlers = {
        "register": handle_register,
        "login": handle_login,
        "guest": handle_guest,
        "quit": handle_quit,
    }

    while True:
        print(menu, end="")
        choice = input(ansi.PROMPT_ARROW).strip().lower()
        handler_key = alias_lookup.get(choice)
        if not handler_key:
            print(f"{ansi.COLOR_WARN}Opción no válida. Probá otra vez.{ansi.RESET}")
            continue

        handler = handlers[handler_key]
        result = handler()
        if result:
            return result


async def _drain_initial_lines(reader: asyncio.StreamReader, timeout: float = 0.15) -> None:
    while True:
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=timeout)
        except asyncio.TimeoutError:
            break
        if not line:
            break
        print(line.decode("utf-8", errors="replace"), end="")


async def _auth_handshake(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> bool:
    while True:
        command = _prompt_initial_command()
        writer.write((command + "\n").encode("utf-8", errors="replace"))
        await writer.drain()

        while True:
            line = await reader.readline()
            if not line:
                print("[Servidor desconectado]")
                return False
            text = line.decode("utf-8", errors="replace")
            print(text, end="")

            lowered = text.lower()
            if any(marker in lowered for marker in SUCCESS_MARKERS):
                return True
            if any(marker in lowered for marker in FAILURE_MARKERS):
                await _drain_initial_lines(reader)
                break


async def run_client(host: str, port: int, auto: bool = True) -> None:
    reader, writer = await asyncio.open_connection(host, port)

    await _drain_initial_lines(reader)
    if auto:
        success = await _auth_handshake(reader, writer)
        if not success:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            return
    else:
        print("Modo manual: escribí /guest, /register <usuario> <clave> o /login <usuario> <clave>.")

    async def recv_task() -> None:
        while True:
            data = await reader.readline()
            if not data:
                print("[Servidor desconectado]")
                break
            print(data.decode("utf-8", errors="replace"), end="")

    async def send_task() -> None:
        loop = asyncio.get_running_loop()
        while True:
            try:
                line = await loop.run_in_executor(None, lambda: input(ansi.PROMPT_ARROW)) #executor para evitar bloqueo y recv_task siga recibiendo del servidor
            except EOFError:
                break
            writer.write((line + "\n").encode("utf-8", errors="replace"))
            await writer.drain()
            if line.strip().lower() in {"/quit", "/exit"}:
                break

    await asyncio.gather(recv_task(), send_task())
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description="Cliente TCP simple para FitBot")
    parser.add_argument("host", nargs="?", default="127.0.0.1", help="Host del servidor")
    parser.add_argument("port", nargs="?", type=int, default=9000, help="Puerto del servidor")
    parser.add_argument(
        "--no-auto",
        action="store_true",
        help="No enviar comandos automáticos (manejá todo desde la consola)",
    )
    args = parser.parse_args()

    asyncio.run(run_client(args.host, args.port, auto=not args.no_auto))
