"""Rate limiting via Redis. Keys by telegram_id or user identifier."""
import time
from typing import Optional

from core.config import get_settings
from core.redis_client import get_redis


async def check_rate_limit(
    key_prefix: str,
    user_id: int,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int]:
    """
    Returns (allowed, remaining). Uses sliding window with Redis.
    """
    redis = await get_redis()
    key = f"rate:{key_prefix}:{user_id}"
    now = time.time()
    window_start = now - window_seconds

    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window_seconds + 1)
    results = await pipe.execute()
    count = results[2] or 0
    remaining = max(0, limit - count)
    allowed = count <= limit
    return allowed, remaining


async def check_create_task_limit(telegram_id: int) -> tuple[bool, int]:
    s = get_settings()
    return await check_rate_limit(
        "create_task",
        telegram_id,
        s.rate_limit_create_task_per_hour,
        3600,
    )


async def check_create_bid_limit(telegram_id: int) -> tuple[bool, int]:
    s = get_settings()
    return await check_rate_limit(
        "create_bid",
        telegram_id,
        s.rate_limit_create_bid_per_hour,
        3600,
    )


async def check_send_message_limit(telegram_id: int) -> tuple[bool, int]:
    s = get_settings()
    return await check_rate_limit(
        "send_message",
        telegram_id,
        s.rate_limit_send_message_per_minute,
        60,
    )


async def check_verification_limit(telegram_id: int) -> tuple[bool, int]:
    s = get_settings()
    return await check_rate_limit(
        "verification",
        telegram_id,
        s.rate_limit_verification_per_day,
        86400,
    )
