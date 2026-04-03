"""User CRUD and lookup."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import User
from core.models.user import UserRole
from core.security.encryption import get_encryption


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    *,
    phone: str | None = None,
    full_name: str | None = None,
    role: str = UserRole.customer.value,
    city_id: int | None = None,
) -> User:
    enc = get_encryption()
    user = User(
        telegram_id=telegram_id,
        phone_encrypted=enc.encrypt(phone) if phone else None,
        full_name=full_name,
        role=role,
        city_id=city_id,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def update_user_activity(session: AsyncSession, user_id: int) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.last_activity = datetime.utcnow()
        await session.flush()


def get_phone_decrypted(user: User) -> str | None:
    if not user.phone_encrypted:
        return None
    return get_encryption().decrypt(user.phone_encrypted)
