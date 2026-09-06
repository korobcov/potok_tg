import logging

import telebot

from app.config.settings import settings
from app.handlers import admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Telegram Bot...")

    if settings.PROXY_URL:
        telebot.apihelper.proxy = {"https": settings.PROXY_URL}

    bot = telebot.TeleBot(settings.BOT_TOKEN, parse_mode="HTML")
    admin.register_handlers(bot)

    bot.infinity_polling()


if __name__ == "__main__":
    main()
