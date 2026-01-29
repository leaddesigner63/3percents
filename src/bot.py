import asyncio
import logging
from dataclasses import dataclass
from typing import Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import load_config
from storage import PostStorage, StoredPost, eligible_posts

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


@dataclass
class UserState:
    index: int = 0
    last_message_id: int | None = None


class ChannelCarouselBot:
    def __init__(self, storage: PostStorage, channel_id: str) -> None:
        self._storage = storage
        self._channel_id = channel_id
        self._channel_username = channel_id.lstrip("@")
        self._user_state: Dict[int, UserState] = {}

    async def handle_channel_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.channel_post
        if message is None:
            return
        chat_username = message.chat.username or ""
        if str(message.chat_id) != self._channel_id and chat_username != self._channel_username:
            return

        stored = StoredPost(
            message_id=message.message_id,
            kind=self._detect_kind(message),
            file_id=self._extract_file_id(message),
            text=message.text or message.caption,
        )
        self._storage.upsert(stored)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat is None or update.effective_user is None:
            return
        await self._send_post(update.effective_chat.id, update.effective_user.id)

    async def on_nav(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query is None or query.data is None:
            return
        await query.answer()
        chat_id = query.message.chat_id if query.message else None
        user_id = query.from_user.id
        if chat_id is None:
            return
        state = self._user_state.setdefault(user_id, UserState())
        direction = query.data.split(":", maxsplit=1)[-1]
        eligible = eligible_posts(self._storage.load())
        if not eligible:
            await self._replace_message(chat_id, user_id, "Нет доступных постов.")
            return
        if direction == "next":
            state.index = min(state.index + 1, len(eligible) - 1)
        elif direction == "prev":
            state.index = max(state.index - 1, 0)
        await self._send_post(chat_id, user_id)

    async def _send_post(self, chat_id: int, user_id: int) -> None:
        eligible = eligible_posts(self._storage.load())
        if not eligible:
            await self._replace_message(chat_id, user_id, "Нет доступных постов.")
            return
        state = self._user_state.setdefault(user_id, UserState())
        state.index = max(0, min(state.index, len(eligible) - 1))
        post = eligible[state.index]
        markup = self._build_keyboard(state.index, len(eligible))
        await self._replace_message(chat_id, user_id, post, markup)

    async def _replace_message(
        self,
        chat_id: int,
        user_id: int,
        content,
        markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        state = self._user_state.setdefault(user_id, UserState())
        if state.last_message_id is not None:
            try:
                await asyncio.sleep(0)
                await self._delete_message(chat_id, state.last_message_id)
            except BadRequest:
                pass
        message_id = await self._send_content(chat_id, content, markup)
        state.last_message_id = message_id

    async def _delete_message(self, chat_id: int, message_id: int) -> None:
        await self._app.bot.delete_message(chat_id=chat_id, message_id=message_id)

    async def _send_content(
        self,
        chat_id: int,
        content,
        markup: InlineKeyboardMarkup | None,
    ) -> int:
        if isinstance(content, str):
            message = await self._app.bot.send_message(
                chat_id=chat_id,
                text=content,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
            return message.message_id
        if content.kind == "text":
            message = await self._app.bot.send_message(
                chat_id=chat_id,
                text=content.text or "",
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
            return message.message_id
        if content.kind == "photo":
            message = await self._app.bot.send_photo(
                chat_id=chat_id,
                photo=content.file_id,
                caption=content.text,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
            return message.message_id
        if content.kind == "video":
            message = await self._app.bot.send_video(
                chat_id=chat_id,
                video=content.file_id,
                caption=content.text,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
            return message.message_id
        if content.kind == "document":
            message = await self._app.bot.send_document(
                chat_id=chat_id,
                document=content.file_id,
                caption=content.text,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
            return message.message_id
        if content.kind == "audio":
            message = await self._app.bot.send_audio(
                chat_id=chat_id,
                audio=content.file_id,
                caption=content.text,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
            return message.message_id
        if content.kind == "animation":
            message = await self._app.bot.send_animation(
                chat_id=chat_id,
                animation=content.file_id,
                caption=content.text,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
            return message.message_id
        message = await self._app.bot.send_message(
            chat_id=chat_id,
            text=content.text or "",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
        return message.message_id

    def _build_keyboard(self, index: int, total: int) -> InlineKeyboardMarkup:
        buttons = []
        row = []
        if index > 0:
            row.append(InlineKeyboardButton("⬅️ Назад", callback_data="nav:prev"))
        if index < total - 1:
            row.append(InlineKeyboardButton("Вперёд ➡️", callback_data="nav:next"))
        if row:
            buttons.append(row)
        return InlineKeyboardMarkup(buttons)

    def _detect_kind(self, message) -> str:
        if message.photo:
            return "photo"
        if message.video:
            return "video"
        if message.document:
            return "document"
        if message.audio:
            return "audio"
        if message.animation:
            return "animation"
        return "text"

    def _extract_file_id(self, message) -> str | None:
        if message.photo:
            return message.photo[-1].file_id
        if message.video:
            return message.video.file_id
        if message.document:
            return message.document.file_id
        if message.audio:
            return message.audio.file_id
        if message.animation:
            return message.animation.file_id
        return None

    def register(self, app) -> None:
        self._app = app
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CallbackQueryHandler(self.on_nav, pattern=r"^nav:"))
        app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, self.handle_channel_post))


def main() -> None:
    config = load_config()
    storage = PostStorage(config.data_file)
    bot = ChannelCarouselBot(storage, config.channel_id)

    app = ApplicationBuilder().token(config.bot_token).build()
    bot.register(app)

    app.run_polling(allowed_updates=["channel_post", "message", "callback_query"])


if __name__ == "__main__":
    main()
