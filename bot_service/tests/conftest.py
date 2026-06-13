import fakeredis.aioredis
import pytest_asyncio


@pytest_asyncio.fixture
async def fake_redis(monkeypatch):
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.bot.handlers.get_redis", lambda: redis)
    return redis