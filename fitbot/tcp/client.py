import asyncio
import sys


async def run_client(host: str, port: int) -> None:
    reader, writer = await asyncio.open_connection(host, port)

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

    await asyncio.gather(recv_task(), send_task())
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":  # pragma: no cover
    host = "127.0.0.1"
    port = 9000
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("Puerto inválido, usando 9000", file=sys.stderr)
    asyncio.run(run_client(host, port))
