"""Profile and verification."""
from telegram import Update
from telegram.ext import ContextTypes

from core.database import AsyncSessionLocal
from core.monitoring import bot_commands_total
from core.services.user_service import get_user_by_telegram_id
from core.services.city_service import get_active_cities_cached
from core.models.user import UserRole

from bot.keyboards.inline import profile_keyboard


def _profile_text(db_user, city_name: str) -> str:
    """Текст профиля: город, для заказчика — оплачено заказов, для исполнителя — выполнено заказов."""
    if db_user.role == UserRole.customer.value:
        tasks_label = "Оплачено заказов"
    else:
        tasks_label = "Выполнено заказов"
    role_label = "Заказчик" if db_user.role == UserRole.customer.value else "Исполнитель"
    return (
        f"Профиль\n"
        f"Имя: {db_user.full_name or '—'}\n"
        f"Город: {city_name}\n"
        f"Рейтинг: {db_user.rating:.1f}\n"
        f"Верификация: {'Да' if db_user.is_verified else 'Нет'}\n"
        f"{tasks_label}: {db_user.completed_tasks_count}\n"
        f"Роль: {role_label}"
    )


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_commands_total.labels(command="profile").inc()
    user = update.effective_user
    if not user:
        return
    from core.redis_client import record_active_user
    await record_active_user(user.id)

    async with AsyncSessionLocal() as session:
        db_user = await get_user_by_telegram_id(session, user.id)
        cities = await get_active_cities_cached(session)
    if not db_user:
        await update.message.reply_text("Сначала пройдите регистрацию: /start")
        return

    city_name = "не указан"
    if db_user.city_id:
        for c in cities:
            if c.id == db_user.city_id:
                city_name = c.name
                break

    text = _profile_text(db_user, city_name)
    await update.message.reply_text(text, reply_markup=profile_keyboard())
