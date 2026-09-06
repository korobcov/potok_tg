import html
import logging
from typing import Optional, Union
from aiogram import Router, F, Bot
from aiogram.types import (
    BufferedInputFile,
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import BaseFilter, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config.settings import settings
from app.services.parser import download_thumbnail, parse_video_url

logger = logging.getLogger(__name__)

router = Router()


def is_admin(user_id: int) -> bool:
    admin_ids = (
        settings.ADMIN_ID
        if isinstance(settings.ADMIN_ID, list)
        else [settings.ADMIN_ID]
    )
    return user_id in admin_ids


class AdminFilter(BaseFilter):
    async def __call__(
        self, event: Union[Message, CallbackQuery]
    ) -> bool:
        if not event.from_user:
            return False
        return is_admin(event.from_user.id)


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


def build_photo_source(
    thumbnail_bytes: Optional[bytes], thumbnail_url: str
) -> Union[BufferedInputFile, str]:
    if thumbnail_bytes:
        return BufferedInputFile(thumbnail_bytes, filename="thumbnail.jpg")
    return thumbnail_url


@router.message(CommandStart())
async def cmd_start(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этому боту.")
        return
    await message.answer(
        "👋 Привет! Отправьте ссылку на видео (YouTube, VK, TikTok, "
        "Instagram, RuTube) — я подготовлю пост с превью для публикации "
        "в канал."
    )


@router.message(AdminFilter(), F.text)
async def process_video_link(message: Message, state: FSMContext):
    text = message.text.strip()
    if not (text.startswith("http://") or text.startswith("https://")):
        await message.reply(
            "Пожалуйста, отправьте корректную ссылку на видео "
            "(начинающуюся с http:// или https://)."
        )
        return

    # Invalidate any previous pending preview so stale buttons can't
    # publish data that no longer matches what's on screen.
    old_data = await state.get_data()
    old_chat_id = old_data.get("preview_chat_id")
    old_message_id = old_data.get("preview_message_id")
    if old_chat_id and old_message_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=old_chat_id,
                message_id=old_message_id,
                reply_markup=None,
            )
        except Exception:
            pass

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
    thumbnail_bytes = await download_thumbnail(video_data["thumbnail_url"])

    try:
        sent = await message.answer_photo(
            photo=build_photo_source(
                thumbnail_bytes, video_data["thumbnail_url"]
            ),
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
        return

    await state.update_data(
        title=video_data["title"],
        thumbnail_url=video_data["thumbnail_url"],
        thumbnail_bytes=thumbnail_bytes,
        url=video_data["url"],
        caption=caption,
        preview_chat_id=sent.chat.id,
        preview_message_id=sent.message_id,
    )


@router.callback_query(F.data == "publish_post")
async def publish_post_callback(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return

    data = await state.get_data()
    if not data or "thumbnail_url" not in data or "caption" not in data:
        await callback.answer(
            "Ошибка: Данные поста устарели или не найдены.", show_alert=True
        )
        return

    try:
        await bot.send_photo(
            chat_id=settings.CHANNEL_ID,
            photo=build_photo_source(
                data.get("thumbnail_bytes"), data["thumbnail_url"]
            ),
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
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply("🚫 Публикация отменена.")
    await callback.answer()
