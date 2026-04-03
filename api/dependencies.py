"""FastAPI dependencies: DB session, Redis, etc."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
