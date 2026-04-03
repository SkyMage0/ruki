"""Rate limit: store telegram_id in context for handlers to check."""

from telegram import Update
from telegram.ext import ContextTypes


async def rate_limit_middleware(
    application, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Post-init: just ensure context has user id for handlers."""
    if update.effective_user:
        context.user_data["telegram_id"] = update.effective_user.id
