import aiosqlite
import asyncio
from typing import List, Dict, Optional

DB_PATH = "fitbot.db"


CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    client_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(client_id) REFERENCES sessions(client_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_messages_client_time ON messages(client_id, created_at);
"""


async def init_db(db_path: Optional[str] = None) -> None:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        # Ejecuta tablas e índices; aiosqlite.execute solo acepta una sentencia,
        # por eso usamos executescript para el bloque con 2 statements.
        await db.execute(CREATE_SESSIONS)
        await db.executescript(CREATE_MESSAGES)
        await db.commit()


async def upsert_session(client_id: str, db_path: Optional[str] = None) -> None:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO sessions(client_id) VALUES (?)",
            (client_id,),
        )
        await db.commit()


async def append_message(client_id: str, role: str, content: str, db_path: Optional[str] = None) -> None:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        await db.execute(
            "INSERT INTO messages(client_id, role, content) VALUES (?,?,?)",
            (client_id, role, content),
        )
        await db.commit()


async def get_history(client_id: str, limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, str]]:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        # Fetch latest 'limit' then return in chronological order
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE client_id = ? ORDER BY id DESC LIMIT ?",
            (client_id, limit),
        )
        rows = await cursor.fetchall()
        await cursor.close()
    # Reverse to chronological
    rows.reverse()
    return [{"role": r[0], "content": r[1]} for r in rows]

