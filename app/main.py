import logging
import sys

from app.runtime_paths import ENV_FILE, IS_FROZEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _wait_for_exit(code: int) -> None:
    # A double-clicked .exe's console window closes the instant the process
    # exits, so a startup/crash message would flash by unread without this.
    if IS_FROZEN:
        input("\nНажмите Enter, чтобы закрыть окно...")
    sys.exit(code)


def _ensure_env_file() -> bool:
    """Create .env from .env.example next to the exe on first run.

    Returns True if the caller should stop and let the user fill it in.
    """
    if ENV_FILE.is_file():
        return False

    example = ENV_FILE.parent / ".env.example"
    if example.is_file():
        ENV_FILE.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        print(
            f"Файл настроек создан: {ENV_FILE}\n"
            "Откройте его в блокноте, укажите BOT_TOKEN, ADMIN_ID и "
            "CHANNEL_ID, сохраните и запустите бота снова."
        )
    else:
        print(
            f"Не найден файл настроек {ENV_FILE} и шаблон .env.example "
            "рядом с ним. Создайте .env вручную (см. README) и запустите "
            "бота снова."
        )
    return True


def main():
    if _ensure_env_file():
        _wait_for_exit(1)

    from pydantic import ValidationError

    try:
        from app.config.settings import settings
    except ValidationError as e:
        print(f"Ошибка в файле настроек {ENV_FILE}:\n{e}")
        _wait_for_exit(1)
        return

    import telebot

    from app.handlers import admin

    logger.info("Starting Telegram Bot...")

    if settings.PROXY_URL:
        telebot.apihelper.proxy = {"https": settings.PROXY_URL}

    bot = telebot.TeleBot(settings.BOT_TOKEN, parse_mode="HTML")
    admin.register_handlers(bot)

    try:
        bot.infinity_polling()
    except Exception:
        logger.exception("Bot crashed")
        _wait_for_exit(1)


if __name__ == "__main__":
    main()
