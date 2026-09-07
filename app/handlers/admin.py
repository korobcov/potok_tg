import html
import logging
import threading
from typing import Dict, Optional, Union

import telebot
from telebot import types

from app.config.settings import settings
from app.services.parser import download_thumbnail, parse_video_url
from app.services.post_footer import get_post_footer

logger = logging.getLogger(__name__)

# In-memory per-admin pending-post state, keyed by admin user id. Lost on
# restart (no persistent storage), same trade-off the previous FSM had.
# telebot's threaded update processing means two updates from the same
# admin can run concurrently, so access is guarded by a lock.
_pending_posts: Dict[int, Dict] = {}
_state_lock = threading.Lock()


def is_admin(user_id: int) -> bool:
    admin_ids = (
        settings.ADMIN_ID
        if isinstance(settings.ADMIN_ID, list)
        else [settings.ADMIN_ID]
    )
    return user_id in admin_ids


def format_post_caption(title: str, url: str) -> str:
    safe_title = html.escape(title)
    caption = f"<b>{safe_title}</b>\n\n🔗 <a href=\"{url}\">Смотреть видео</a>"

    footer = get_post_footer()
    if footer:
        # Not escaped on purpose: this is admin-authored config content
        # (see post_footer.example.txt), not external input, and it's
        # meant to use Telegram's own HTML formatting (bold, spoiler,
        # blockquote, links, ...).
        caption += f"\n\n{footer}"
    return caption


def get_post_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton(
            "📢 Опубликовать в канал", callback_data="publish_post"
        ),
        types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_post"),
    )
    keyboard.row(
        types.InlineKeyboardButton(
            "✏️ Изменить описание", callback_data="edit_caption"
        ),
    )
    return keyboard


def build_photo_source(
    thumbnail_bytes: Optional[bytes], thumbnail_url: str
) -> Union[bytes, str]:
    return thumbnail_bytes if thumbnail_bytes else thumbnail_url


def _apply_caption_edit(
    bot: telebot.TeleBot, message: types.Message, data: Dict
) -> None:
    new_title = message.text.strip()
    if not new_title:
        bot.reply_to(
            message, "Текст не может быть пустым. Отправьте описание ещё раз."
        )
        return

    caption = format_post_caption(new_title, data["url"])

    with _state_lock:
        data["title"] = new_title
        data["caption"] = caption
        data["awaiting_caption"] = False

    try:
        bot.edit_message_caption(
            caption=f"📋 <b>Предпросмотр поста:</b>\n\n{caption}",
            chat_id=data["preview_chat_id"],
            message_id=data["preview_message_id"],
            parse_mode="HTML",
            reply_markup=get_post_keyboard(),
        )
        bot.reply_to(message, "✅ Описание обновлено, превью выше обновлено.")
    except Exception as e:
        logger.error(f"Error updating preview caption: {e}")
        bot.reply_to(
            message, f"❌ Не удалось обновить превью.\nОшибка: {e}"
        )


def register_handlers(bot: telebot.TeleBot) -> None:

    @bot.message_handler(commands=["start"])
    def cmd_start(message: types.Message):
        if not message.from_user or not is_admin(message.from_user.id):
            bot.send_message(
                message.chat.id, "⛔ У вас нет доступа к этому боту."
            )
            return
        bot.send_message(
            message.chat.id,
            "👋 Привет! Отправьте ссылку на видео (YouTube, VK, TikTok, "
            "Instagram, RuTube) — я подготовлю пост с превью для "
            "публикации в канал.",
        )

    @bot.message_handler(content_types=["text"])
    def process_video_link(message: types.Message):
        if not message.from_user or not is_admin(message.from_user.id):
            return

        user_id = message.from_user.id

        with _state_lock:
            pending = _pending_posts.get(user_id)
            awaiting_caption = bool(
                pending and pending.get("awaiting_caption")
            )

        if awaiting_caption:
            _apply_caption_edit(bot, message, pending)
            return

        text = message.text.strip()
        if not (text.startswith("http://") or text.startswith("https://")):
            bot.reply_to(
                message,
                "Пожалуйста, отправьте корректную ссылку на видео "
                "(начинающуюся с http:// или https://).",
            )
            return

        # Invalidate any previous pending preview so stale buttons can't
        # publish data that no longer matches what's on screen.
        with _state_lock:
            old_data = _pending_posts.get(user_id)
        if old_data:
            try:
                bot.edit_message_reply_markup(
                    chat_id=old_data["preview_chat_id"],
                    message_id=old_data["preview_message_id"],
                    reply_markup=None,
                )
            except Exception:
                pass

        status_msg = bot.reply_to(message, "⏳ Парсим информацию о видео...")

        video_data = parse_video_url(text)
        try:
            bot.delete_message(status_msg.chat.id, status_msg.message_id)
        except Exception:
            pass

        if not video_data:
            bot.reply_to(
                message,
                "❌ Не удалось обработать ссылку или извлечь превью.\n"
                "Убедитесь, что ссылка ведет на поддерживаемый ресурс "
                "(YouTube, VK, TikTok, Instagram, RuTube) "
                "и видео доступно публично.",
            )
            return

        caption = format_post_caption(video_data["title"], video_data["url"])
        thumbnail_bytes = download_thumbnail(video_data["thumbnail_url"])

        try:
            sent = bot.send_photo(
                message.chat.id,
                photo=build_photo_source(
                    thumbnail_bytes, video_data["thumbnail_url"]
                ),
                caption=f"📋 <b>Предпросмотр поста:</b>\n\n{caption}",
                parse_mode="HTML",
                reply_markup=get_post_keyboard(),
            )
        except Exception as e:
            logger.error(f"Error sending preview photo: {e}")
            bot.reply_to(
                message,
                f"❌ Не удалось загрузить предпросмотр превью по URL.\n"
                f"Ошибка: {e}",
            )
            return

        with _state_lock:
            _pending_posts[user_id] = {
                "title": video_data["title"],
                "url": video_data["url"],
                "thumbnail_url": video_data["thumbnail_url"],
                "thumbnail_bytes": thumbnail_bytes,
                "caption": caption,
                "preview_chat_id": sent.chat.id,
                "preview_message_id": sent.message_id,
            }

    @bot.callback_query_handler(func=lambda c: c.data == "publish_post")
    def publish_post_callback(call: types.CallbackQuery):
        if not call.from_user or not is_admin(call.from_user.id):
            bot.answer_callback_query(
                call.id, "⛔ Доступ запрещён.", show_alert=True
            )
            return

        with _state_lock:
            data = _pending_posts.get(call.from_user.id)

        if not data:
            bot.answer_callback_query(
                call.id,
                "Ошибка: Данные поста устарели или не найдены.",
                show_alert=True,
            )
            return

        try:
            bot.send_photo(
                settings.CHANNEL_ID,
                photo=build_photo_source(
                    data.get("thumbnail_bytes"), data["thumbnail_url"]
                ),
                caption=data["caption"],
                parse_mode="HTML",
            )
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None,
            )
            bot.send_message(
                call.message.chat.id, "✅ Успешно опубликовано в канал!"
            )
            with _state_lock:
                _pending_posts.pop(call.from_user.id, None)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(
                f"Failed to publish to channel {settings.CHANNEL_ID}: {e}"
            )
            bot.send_message(
                call.message.chat.id,
                f"❌ Ошибка при публикации в канал: {e}",
            )
            bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "edit_caption")
    def edit_caption_callback(call: types.CallbackQuery):
        if not call.from_user or not is_admin(call.from_user.id):
            bot.answer_callback_query(
                call.id, "⛔ Доступ запрещён.", show_alert=True
            )
            return

        with _state_lock:
            data = _pending_posts.get(call.from_user.id)
            if data:
                data["awaiting_caption"] = True

        if not data:
            bot.answer_callback_query(
                call.id,
                "Ошибка: Данные поста устарели или не найдены.",
                show_alert=True,
            )
            return

        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "✏️ Отправьте новый текст для поста (замените заголовок/"
            "описание). Следующее сообщение будет использовано как текст "
            "поста.",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "cancel_post")
    def cancel_post_callback(call: types.CallbackQuery):
        if not call.from_user or not is_admin(call.from_user.id):
            bot.answer_callback_query(
                call.id, "⛔ Доступ запрещён.", show_alert=True
            )
            return

        with _state_lock:
            _pending_posts.pop(call.from_user.id, None)
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None,
        )
        bot.send_message(call.message.chat.id, "🚫 Публикация отменена.")
        bot.answer_callback_query(call.id)
