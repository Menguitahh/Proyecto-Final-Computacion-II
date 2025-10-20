import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_SESSIONS_KEY = "fitbot:sessions"
_MESSAGES_KEY_FMT = "fitbot:session:{client_id}:messages"
_WORKOUTS_KEY_FMT = "fitbot:session:{client_id}:workouts"

_redis: Optional[redis.Redis] = None


def _messages_key(client_id: str) -> str:
    return _MESSAGES_KEY_FMT.format(client_id=client_id)


def _workouts_key(client_id: str) -> str:
    return _WORKOUTS_KEY_FMT.format(client_id=client_id)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db(url: Optional[str] = None, client: Optional[redis.Redis] = None) -> None:
    """Inicializa la conexión global a Redis (o inyecta un cliente para pruebas)."""
    global _redis
    if client is not None:
        _redis = client
        return

    redis_url = url or REDIS_URL
    _redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    await _redis.ping()


async def close() -> None:
    """Cierra la conexión global si existe."""
    global _redis
    if _redis is not None:
        try:
            await _redis.close()
        finally:
            _redis = None


def _require_client(client: Optional[redis.Redis] = None) -> redis.Redis:
    conn = client or _redis
    if conn is None:
        raise RuntimeError("Redis no inicializado. Llamá chat_store.init_db() en el arranque.")
    return conn


async def upsert_session(client_id: str, client: Optional[redis.Redis] = None) -> None:
    conn = _require_client(client)
    await conn.sadd(_SESSIONS_KEY, client_id)


async def append_message(
    client_id: str,
    role: str,
    content: str,
    client: Optional[redis.Redis] = None,
) -> None:
    conn = _require_client(client)
    payload = json.dumps(
        {
            "role": role,
            "content": content,
            "created_at": _utc_now(),
        }
    )
    await conn.rpush(_messages_key(client_id), payload)


async def get_history(
    client_id: str,
    limit: int = 50,
    client: Optional[redis.Redis] = None,
) -> List[Dict[str, Any]]:
    conn = _require_client(client)
    raw_messages = await conn.lrange(_messages_key(client_id), -limit, -1)
    history: List[Dict[str, Any]] = []
    for raw in raw_messages:
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        history.append({"role": entry.get("role", "assistant"), "content": entry.get("content", "")})
    return history


async def clear_history(client_id: str, client: Optional[redis.Redis] = None) -> None:
    conn = _require_client(client)
    await conn.delete(_messages_key(client_id))


async def log_workout(client_id: str, entry: str, client: Optional[redis.Redis] = None) -> None:
    conn = _require_client(client)
    payload = json.dumps({"entry": entry, "created_at": _utc_now()})
    await conn.rpush(_workouts_key(client_id), payload)


async def get_workouts(
    client_id: str,
    limit: int = 10,
    client: Optional[redis.Redis] = None,
) -> List[Dict[str, Any]]:
    conn = _require_client(client)
    raw_entries = await conn.lrange(_workouts_key(client_id), -limit, -1)
    workouts: List[Dict[str, Any]] = []
    for raw in raw_entries:
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        workouts.append(
            {
                "entry": entry.get("entry", ""),
                "created_at": entry.get("created_at"),
            }
        )
    return workouts
