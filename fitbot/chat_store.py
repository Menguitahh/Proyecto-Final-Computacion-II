import aiosqlite
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "fitbot.db")


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

CREATE_PROFILES = """
CREATE TABLE IF NOT EXISTS profiles (
    client_id TEXT PRIMARY KEY,
    goal TEXT,
    experience TEXT,
    equipment TEXT,
    limitations TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(client_id) REFERENCES sessions(client_id) ON DELETE CASCADE
);
"""

CREATE_WORKOUTS = """
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL,
    entry TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(client_id) REFERENCES sessions(client_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_workouts_client_time ON workouts(client_id, created_at);
"""


async def init_db(db_path: Optional[str] = None) -> None:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        # Ejecuta tablas e índices; aiosqlite.execute solo acepta una sentencia,
        # por eso usamos executescript para bloques múltiples.
        await db.execute(CREATE_SESSIONS)
        await db.executescript(CREATE_MESSAGES)
        await db.execute(CREATE_PROFILES)
        await db.executescript(CREATE_WORKOUTS)
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


async def get_all_history(client_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        cursor = await db.execute(
            "SELECT role, content, created_at FROM messages WHERE client_id = ? ORDER BY id ASC",
            (client_id,),
        )
        rows = await cursor.fetchall()
        await cursor.close()
    return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in rows]


async def clear_history(client_id: str, db_path: Optional[str] = None) -> None:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        await db.execute("DELETE FROM messages WHERE client_id = ?", (client_id,))
        await db.commit()


# Perfil de usuario
async def upsert_profile(client_id: str, goal: Optional[str], experience: Optional[str], equipment: Optional[str], limitations: Optional[str], db_path: Optional[str] = None) -> None:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        await db.execute(
            "INSERT INTO profiles(client_id, goal, experience, equipment, limitations) VALUES (?,?,?,?,?)\n"
            "ON CONFLICT(client_id) DO UPDATE SET goal=excluded.goal, experience=excluded.experience, equipment=excluded.equipment, limitations=excluded.limitations, updated_at=CURRENT_TIMESTAMP",
            (client_id, goal, experience, equipment, limitations),
        )
        await db.commit()


async def get_profile(client_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Optional[str]]]:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        cursor = await db.execute(
            "SELECT goal, experience, equipment, limitations FROM profiles WHERE client_id = ?",
            (client_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
    if not row:
        return None
    return {"goal": row[0], "experience": row[1], "equipment": row[2], "limitations": row[3]}


# Workouts simples
async def log_workout(client_id: str, entry: str, db_path: Optional[str] = None) -> None:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        await db.execute("INSERT INTO workouts(client_id, entry) VALUES (?,?)", (client_id, entry))
        await db.commit()


async def get_workouts(client_id: str, limit: int = 10, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        cursor = await db.execute(
            "SELECT entry, created_at FROM workouts WHERE client_id = ? ORDER BY id DESC LIMIT ?",
            (client_id, limit),
        )
        rows = await cursor.fetchall()
        await cursor.close()
    rows.reverse()
    return [{"entry": r[0], "created_at": r[1]} for r in rows]

