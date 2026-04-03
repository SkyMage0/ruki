"""Support link."""

from telegram import Update
from telegram.ext import ContextTypes

from core.monitoring import bot_commands_total

SUPPORT_TEXT = (
    "По вопросам работы сервиса обращайтесь в поддержку.\n"
    "Напишите сюда: @support_ruki (замените на ваш контакт)"
)


async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_commands_total.labels(command="support").inc()
    await update.message.reply_text(SUPPORT_TEXT)
