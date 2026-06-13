from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.core.config import settings


def create_bot() -> Bot:
    return Bot(token=settings.TELEGRAM_BOT_TOKEN)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp