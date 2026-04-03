"""Redis connection for cache and rate limiting."""

import os

import redis.asyncio as redis
from redis.asyncio import Redis

from core.config import get_settings

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL") or get_settings().redis_url
        _redis = redis.from_url(url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


ACTIVE_USERS_ZSET = "active_users_zset"
ACTIVE_WINDOW = 3600  # 1 hour


async def record_active_user(telegram_id: int) -> None:
    """Record user activity for active_users_gauge (last hour)."""
    import time

    r = await get_redis()
    now = time.time()
    await r.zadd(ACTIVE_USERS_ZSET, {str(telegram_id): now})
    await r.zremrangebyscore(ACTIVE_USERS_ZSET, 0, now - ACTIVE_WINDOW)
    await r.expire(ACTIVE_USERS_ZSET, ACTIVE_WINDOW + 60)


async def get_active_users_count() -> int:
    """Count distinct users active in last hour."""
    import time

    r = await get_redis()
    now = time.time()
    await r.zremrangebyscore(ACTIVE_USERS_ZSET, 0, now - ACTIVE_WINDOW)
    return await r.zcard(ACTIVE_USERS_ZSET)
