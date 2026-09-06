import html
import logging
from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config.settings import settings
from app.services.parser import parse_video_url

logger = logging.getLogger(__name__)

router = Router()


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        admin_ids = (
            settings.ADMIN_ID
            if isinstance(settings.ADMIN_ID, list)
            else [settings.ADMIN_ID]
        )
        return message.from_user.id in admin_ids


class PostStates(StatesGroup):
    confirm_publish = State()


def get_post_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Опубликовать в канал",
                    callback_data="publish_post",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel_post",
                ),
            ]
        ]
    )
    return keyboard


def format_post_caption(title: str, url: str) -> str:
    safe_title = html.escape(title)
    return f"<b>{safe_title}</b>\n\n🔗 <a href=\"{url}\">Смотреть видео</a>"


@router.message(AdminFilter(), F.text)
async def process_video_link(message: Message, state: FSMContext):
    text = message.text.strip()
    if not (text.startswith("http://") or text.startswith("https://")):
        await message.reply(
            "Пожалуйста, отправьте корректную ссылку на видео "
            "(начинающуюся с http:// или https://)."
        )
        return

    status_msg = await message.reply("⏳ Парсим информацию о видео...")

    video_data = await parse_video_url(text)
    await status_msg.delete()

    if not video_data:
        await message.reply(
            "❌ Не удалось обработать ссылку или извлечь превью.\n"
            "Убедитесь, что ссылка ведет на поддерживаемый ресурс "
            "(YouTube, VK, TikTok, Instagram, RuTube) "
            "и видео доступно публично."
        )
        return

    caption = format_post_caption(video_data["title"], video_data["url"])
    await state.update_data(
        title=video_data["title"],
        thumbnail_url=video_data["thumbnail_url"],
        url=video_data["url"],
        caption=caption,
    )

    try:
        await message.answer_photo(
            photo=video_data["thumbnail_url"],
            caption=f"📋 <b>Предпросмотр поста:</b>\n\n{caption}",
            parse_mode="HTML",
            reply_markup=get_post_keyboard(),
        )
    except Exception as e:
        logger.error(f"Error sending preview photo: {e}")
        await message.reply(
            f"❌ Не удалось загрузить предпросмотр превью по URL.\n"
            f"Ошибка: {e}"
        )


@router.callback_query(F.data == "publish_post")
async def publish_post_callback(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    data = await state.get_data()
    if not data or "thumbnail_url" not in data or "caption" not in data:
        await callback.answer(
            "Ошибка: Данные поста устарели или не найдены.", show_alert=True
        )
        return

    try:
        await bot.send_photo(
            chat_id=settings.CHANNEL_ID,
            photo=data["thumbnail_url"],
            caption=data["caption"],
            parse_mode="HTML",
        )
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply("✅ Успешно опубликовано в канал!")
        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.error(
            f"Failed to publish to channel {settings.CHANNEL_ID}: {e}"
        )
        await callback.message.reply(
            f"❌ Ошибка при публикации в канал: {e}"
        )
        await callback.answer()


@router.callback_query(F.data == "cancel_post")
async def cancel_post_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply("🚫 Публикация отменена.")
    await callback.answer()
