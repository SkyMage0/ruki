"""Telegram Bot entry point. Sentry + logging. No PII in logs."""

import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.handlers import profile, start, support, tasks
from core.config import get_settings
from core.monitoring import configure_logging, get_logger, init_sentry

configure_logging()
init_sentry()
logger = get_logger()

# Reduce noise from libs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


async def main_menu_router(update, context):
    """Обработка кнопок главного меню."""
    text = (update.message and update.message.text) or ""
    if text == "Создать заказ":
        return await tasks.cmd_new_task(update, context)
    if text == "Мои заказы":
        return await tasks.cmd_my_tasks(update, context)
    if text == "Найти работу":
        return await tasks.cmd_tasks(update, context)
    if text == "Мои отклики":
        return await tasks.cmd_my_tasks(update, context)
    if text == "Профиль":
        return await profile.cmd_profile(update, context)
    if text == "Поддержка":
        return await support.cmd_support(update, context)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN") or get_settings().telegram_bot_token
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start.cmd_start))
    app.add_handler(CommandHandler("new_task", tasks.cmd_new_task))
    app.add_handler(CommandHandler("my_tasks", tasks.cmd_my_tasks))
    app.add_handler(CommandHandler("tasks", tasks.cmd_tasks))
    app.add_handler(CommandHandler("profile", profile.cmd_profile))
    app.add_handler(CommandHandler("support", support.cmd_support))

    app.add_handler(CallbackQueryHandler(tasks.handle_callback))
    app.add_handler(MessageHandler(filters.CONTACT, start.handle_contact))

    # Главное меню (reply-кнопки)
    menu_filter = (
        filters.TEXT
        & ~filters.COMMAND
        & (
            filters.Regex("^Создать заказ$")
            | filters.Regex("^Мои заказы$")
            | filters.Regex("^Найти работу$")
            | filters.Regex("^Мои отклики$")
            | filters.Regex("^Профиль$")
            | filters.Regex("^Поддержка$")
        )
    )
    app.add_handler(MessageHandler(menu_filter, main_menu_router))

    # Conversation: new_task flow + вопросы/ответы
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tasks.handle_text))

    logger.info("bot_starting")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
