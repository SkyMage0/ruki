"""Registration: /start — request phone, city, role."""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from core.database import AsyncSessionLocal
from core.monitoring import bot_commands_total, get_logger
from core.services.user_service import get_user_by_telegram_id, create_user
from core.services.city_service import get_active_cities_cached

logger = get_logger()


def _main_menu_keyboard(role: str) -> ReplyKeyboardMarkup:
    """Главное меню с клавиатурой по роли."""
    if role == "customer":
        buttons = [
            [KeyboardButton("Создать заказ"), KeyboardButton("Мои заказы")],
            [KeyboardButton("Профиль"), KeyboardButton("Поддержка")],
        ]
    else:
        buttons = [
            [KeyboardButton("Найти работу"), KeyboardButton("Мои отклики")],
            [KeyboardButton("Профиль"), KeyboardButton("Поддержка")],
        ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_commands_total.labels(command="start").inc()
    user = update.effective_user
    if not user:
        return
    from core.redis_client import record_active_user
    await record_active_user(user.id)

    async with AsyncSessionLocal() as session:
        existing = await get_user_by_telegram_id(session, user.id)
        if existing:
            if existing.role == "customer":
                text = (
                    f"Снова здравствуйте, {existing.full_name or user.first_name or 'друг'}!\n\n"
                    "Вы зарегистрированы как заказчик."
                )
            else:
                text = (
                    f"Снова здравствуйте, {existing.full_name or user.first_name or 'друг'}!\n\n"
                    "Вы зарегистрированы как исполнитель."
                )
            await update.message.reply_text(text, reply_markup=_main_menu_keyboard(existing.role))
            return

        # Request contact
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("Отправить номер телефона", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            "Добро пожаловать в «Свободные руки»!\n"
            "Для регистрации отправьте номер телефона (кнопка ниже).",
            reply_markup=keyboard,
        )
        context.user_data["register_step"] = "phone"


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle shared contact after /start."""
    if context.user_data.get("register_step") != "phone":
        return
    contact = update.message.contact
    if not contact or not contact.phone_number:
        await update.message.reply_text("Не удалось получить номер. Нажмите кнопку «Отправить номер телефона». ")
        return

    phone = contact.phone_number
    context.user_data["phone"] = phone
    context.user_data["register_step"] = "city"

    async with AsyncSessionLocal() as session:
        cities = await get_active_cities_cached(session)
    if not cities:
        await update.message.reply_text("Нет активных городов. Обратитесь в поддержку: /support")
        context.user_data["register_step"] = None
        return

    from bot.keyboards.inline import cities_keyboard
    await update.message.reply_text("Выберите город:", reply_markup=cities_keyboard(cities))


async def handle_role_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, city_id: int) -> None:
    """After city chosen: ask role."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    context.user_data["city_id"] = city_id
    context.user_data["register_step"] = "role"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Заказчик", callback_data="role:customer")],
        [InlineKeyboardButton("Исполнитель", callback_data="role:worker")],
    ])
    await update.callback_query.edit_message_text("Кем вы будете пользоваться сервисом?", reply_markup=kb)
