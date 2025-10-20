import pytest
import fakeredis.aioredis

from fitbot import chat_store


@pytest.mark.asyncio
async def test_chat_store_roundtrip():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await chat_store.init_db(client=client)
    cid = 'testuser'
    await chat_store.upsert_session(cid)
    await chat_store.append_message(cid, 'user', 'hola')
    await chat_store.append_message(cid, 'assistant', 'hola!')
    hist = await chat_store.get_history(cid, limit=10)
    assert len(hist) == 2
    assert hist[0]['role'] == 'user' and 'hola' in hist[0]['content']
    assert hist[1]['role'] == 'assistant'

    # workouts
    await chat_store.log_workout(cid, 'pushups 3x10')
    w = await chat_store.get_workouts(cid)
    assert w and 'pushups' in w[-1]['entry']

    await chat_store.clear_history(cid)
    assert await chat_store.get_history(cid) == []

    await client.flushall()
    await client.close()
    await chat_store.close()
