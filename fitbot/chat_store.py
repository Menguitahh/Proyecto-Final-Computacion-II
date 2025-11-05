import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_SESSIONS_KEY = "fitbot:sessions"
_USERS_KEY = "fitbot:users"
_MESSAGES_KEY_FMT = "fitbot:session:{client_id}:messages"
_WORKOUTS_KEY_FMT = "fitbot:session:{client_id}:workouts"
_USER_KEY_FMT = "fitbot:user:{username}"

_redis: Optional[redis.Redis] = None


def _messages_key(client_id: str) -> str:
    return _MESSAGES_KEY_FMT.format(client_id=client_id)


def _workouts_key(client_id: str) -> str:
    return _WORKOUTS_KEY_FMT.format(client_id=client_id)


def _user_key(username: str) -> str:
    return _USER_KEY_FMT.format(username=username)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db(url: Optional[str] = None, client: Optional[redis.Redis] = None) -> None:
    global _redis
    if client is not None:
        _redis = client
        return

    redis_url = url or REDIS_URL
    _redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    await _redis.ping()


async def close() -> None:
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


async def register_user(
    username: str,
    password_hash: str,
    client_id: Optional[str] = None,
    client: Optional[redis.Redis] = None,
) -> str:
    conn = _require_client(client)
    key = _user_key(username)
    exists = await conn.exists(key)
    if exists:
        raise ValueError("Usuario ya existe")

    assigned_client_id = client_id or f"user-{secrets.token_hex(6)}"
    payload = json.dumps(
        {
            "username": username,
            "password_hash": password_hash,
            "client_id": assigned_client_id,
            "created_at": _utc_now(),
        }
    )

    async with conn.pipeline() as pipe:
        pipe.sadd(_USERS_KEY, username)
        pipe.set(key, payload)
        await pipe.execute()

    await upsert_session(assigned_client_id, client=conn)
    return assigned_client_id


async def get_user(username: str, client: Optional[redis.Redis] = None) -> Optional[Dict[str, Any]]:
    conn = _require_client(client)
    raw = await conn.get(_user_key(username))
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data


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
