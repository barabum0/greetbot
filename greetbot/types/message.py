import asyncio
import textwrap
from html import escape
from typing import Self, TYPE_CHECKING

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, BufferedInputFile, User, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.formatting import Text
from aiogram.utils.media_group import MediaGroupBuilder
from pydantic import BaseModel

from greetbot.services.placeholders import apply_user_info
from greetbot.types.extra.file import Base64File
from greetbot.types.media import MediaFile, MediaDataType

if TYPE_CHECKING:
    from greetbot.types.survey import AnswerVariant


class DatabaseMessage(BaseModel):
    caption: str | None = None
    media_files: list[MediaFile]
    send_delay_seconds: int = 0

    @classmethod
    async def from_messages(cls, messages: list[Message], bot: Bot) -> Self:
        media_files: list[MediaFile] = []
        caption: str | None = None

        for message in messages:
            if message.photo is not None:
                data = await bot.download(message.photo[-1].file_id)
                data_bytes = data.read()  # type: ignore
                media_files.append(MediaFile(data_type=MediaDataType.IMAGE, base64=Base64File.from_bytes(data_bytes)))
            elif message.video is not None:
                data = await bot.download(message.video.file_id)
                data_bytes = data.read()  # type: ignore
                media_files.append(MediaFile(data_type=MediaDataType.VIDEO, base64=Base64File.from_bytes(data_bytes)))
            elif message.document is not None:
                data = await bot.download(message.document.file_id)
                data_bytes = data.read()  # type: ignore
                mf = MediaFile(data_type=MediaDataType.DOCUMENT, base64=Base64File.from_bytes(data_bytes),
                                             file_name=message.document.file_name or "file.txt")
                if message.document.thumbnail is not None:
                    thumbnail_data = await bot.download(message.document.thumbnail.file_id)
                    thumbnail_data_bytes = thumbnail_data.read()  # type: ignore
                    mf.thumbnail_base64 = Base64File.from_bytes(thumbnail_data_bytes)

                media_files.append(mf)

            if caption is None:
                caption = message.html_text

        return cls(caption=caption, media_files=media_files)

    async def send_as_aiogram_message(self, bot: Bot, chat_id: int, user: User, test_case: bool = False) -> None:
        await asyncio.sleep(self.send_delay_seconds)

        reply_markup: InlineKeyboardMarkup | None = None
        if hasattr(self, "is_survey") and hasattr(self, "survey_answer_variants") and hasattr(self,
                                                                                              "id") and self.is_survey is True:
            self.survey_answer_variants: list["AnswerVariant"]
            keyboard = [
                [InlineKeyboardButton(text=s.answer_text,
                                      callback_data=f"survey_answer_{self.id}_{s.answer_id}" if not test_case else "pass")]
                for s in self.survey_answer_variants
            ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        if len(self.media_files) == 0 and self.caption is not None:
            await bot.send_message(chat_id=chat_id, text=apply_user_info(user, self.caption) or "",
                                   reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            return
        elif len(self.media_files) > 0:
            media_group = MediaGroupBuilder(caption=apply_user_info(user, self.caption))
            for media in self.media_files:
                file = BufferedInputFile(file=media.base64.to_bytes(), filename=media.file_name or "file")

                media_group.add(type=media.data_type.value, media=file, has_spoiler=media.in_spoiler, thumbnail=file)  # type: ignore

            await bot.send_media_group(chat_id, media=media_group.build())

    @property
    def settings_report(self) -> str:
        output = ""
        if self.send_delay_seconds != 0:
            output += f"Задержка перед отправкой: {self.send_delay_seconds} секунд\n"
        if self.caption:
            output += f"Текст: {escape(textwrap.shorten(self.caption.strip(), width=20, placeholder='...'), quote=False)}"

        photo_count = sum(1 for m in self.media_files if m.data_type is MediaDataType.IMAGE)
        video_count = sum(1 for m in self.media_files if m.data_type is MediaDataType.VIDEO)
        document_count = sum(1 for m in self.media_files if m.data_type is MediaDataType.DOCUMENT)

        if photo_count > 0:
            output += f"\nКол-во фотографий: {photo_count}"
        if video_count > 0:
            output += f"\nКол-во фотографий: {video_count}"
        if document_count > 0:
            output += f"\nКол-во документов: {document_count}"
        if hasattr(self, "is_survey") and self.is_survey is True:
            output += f"\nЯвляется опросом"

        return output.strip()


class CopyMessage(BaseModel):
    from_chat_id: int
    message_id: int

    @classmethod
    async def from_message(cls, message: Message) -> Self:
        return cls(
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
