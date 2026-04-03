"""City listing and CRUD. Cache active cities in Redis."""
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import City
from core.redis_client import get_redis
import json

CACHE_KEY_ACTIVE_CITIES = "cache:active_cities"
CACHE_TTL = 3600  # 1 hour


async def get_active_cities_cached(session: AsyncSession) -> List[City]:
    redis = await get_redis()
    raw = await redis.get(CACHE_KEY_ACTIVE_CITIES)
    if raw:
        try:
            data = json.loads(raw)
            return [City(id=c["id"], name=c["name"], timezone=c.get("timezone", "Europe/Moscow"), is_active=True) for c in data]
        except Exception:
            pass
    result = await session.execute(
        select(City).where(City.is_active == True).order_by(City.name)
    )
    cities = list(result.scalars().all())
    await redis.setex(
        CACHE_KEY_ACTIVE_CITIES,
        CACHE_TTL,
        json.dumps([{"id": c.id, "name": c.name, "timezone": c.timezone} for c in cities]),
    )
    return cities


async def get_active_cities_db_only(session: AsyncSession) -> List[City]:
    result = await session.execute(
        select(City).where(City.is_active == True).order_by(City.name)
    )
    return list(result.scalars().all())


async def get_city_by_id(session: AsyncSession, city_id: int):
    result = await session.execute(select(City).where(City.id == city_id))
    return result.scalar_one_or_none()


async def invalidate_cities_cache() -> None:
    redis = await get_redis()
    await redis.delete(CACHE_KEY_ACTIVE_CITIES)
