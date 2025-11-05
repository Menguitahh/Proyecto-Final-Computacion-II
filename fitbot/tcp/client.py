import argparse
import asyncio
import getpass
import sys
from typing import List

RESET = "\033[0m"
BOLD = "\033[1m"
COLOR_INFO = "\033[94m"
COLOR_SUCCESS = "\033[92m"
COLOR_WARN = "\033[93m"
COLOR_PROMPT = "\033[96m"

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
        f"\n{COLOR_INFO}{BOLD}Elegí cómo querés iniciar:{RESET}\n"
        f"  {COLOR_SUCCESS}[1]{RESET} Registrarme (usuario nuevo)\n"
        f"  {COLOR_SUCCESS}[2]{RESET} Iniciar sesión\n"
        f"  {COLOR_SUCCESS}[3]{RESET} Continuar como invitado "
        f"{COLOR_WARN}(no se guarda historial){RESET}\n"
        f"  {COLOR_SUCCESS}[q]{RESET} Salir\n"
    )
    while True:
        print(menu, end="")
        choice = input(f"{COLOR_PROMPT}> {RESET}").strip().lower()
        if choice in {"1", "r", "register", "registro"}:
            username = input(f"{COLOR_INFO}Usuario:{RESET} ").strip()
            if not username or " " in username:
                print(f"{COLOR_WARN}El usuario no puede estar vacío ni contener espacios.{RESET}")
                continue
            password = getpass.getpass(f"{COLOR_INFO}Clave:{RESET} ").strip()
            if not password or " " in password:
                print(f"{COLOR_WARN}La clave no puede estar vacía ni contener espacios.{RESET}")
                continue
            return f"/register {username} {password}"
        if choice in {"2", "l", "login"}:
            username = input(f"{COLOR_INFO}Usuario:{RESET} ").strip()
            password = getpass.getpass(f"{COLOR_INFO}Clave:{RESET} ").strip()
            return f"/login {username} {password}"
        if choice in {"3", "g", "guest", "invitado"}:
            return "/guest"
        if choice in {"q", "quit", "exit", "salir"}:
            print(f"{COLOR_INFO}Hasta la próxima.{RESET}")
            sys.exit(0)
        print(f"{COLOR_WARN}Opción no válida. Probá otra vez.{RESET}")


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
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            writer.write(line.encode("utf-8", errors="replace"))
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
