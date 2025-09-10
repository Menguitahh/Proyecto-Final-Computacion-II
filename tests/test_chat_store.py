import asyncio
import os
import tempfile
import pytest

from fitbot import chat_store


@pytest.mark.asyncio
async def test_chat_store_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        dbp = os.path.join(td, 'test.db')
        await chat_store.init_db(db_path=dbp)
        cid = 'testuser'
        await chat_store.upsert_session(cid, db_path=dbp)
        await chat_store.append_message(cid, 'user', 'hola', db_path=dbp)
        await chat_store.append_message(cid, 'assistant', 'hola!', db_path=dbp)
        hist = await chat_store.get_history(cid, limit=10, db_path=dbp)
        assert len(hist) == 2
        assert hist[0]['role'] == 'user' and 'hola' in hist[0]['content']
        assert hist[1]['role'] == 'assistant'

        # workouts
        await chat_store.log_workout(cid, 'pushups 3x10', db_path=dbp)
        w = await chat_store.get_workouts(cid, db_path=dbp)
        assert w and 'pushups' in w[0]['entry']

