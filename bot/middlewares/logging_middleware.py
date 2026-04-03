"""Log bot events (no PII)."""
from telegram import Update
from telegram.ext import ContextTypes

from core.monitoring import get_logger, bot_commands_total

logger = get_logger()


async def logging_middleware(application, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Increment command metric. No user id or text in logs by default."""
    if update.effective_message and update.effective_message.text:
        text = update.effective_message.text.strip()
        if text.startswith("/"):
            cmd = text.split()[0].lstrip("/") if text else "unknown"
            bot_commands_total.labels(command=cmd).inc()
            logger.info("bot_command", command=cmd)
