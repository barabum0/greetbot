import textwrap
from html import escape
from typing import Self

from aiogram import Bot
from aiogram.types import Message, BufferedInputFile, User
from aiogram.utils.media_group import MediaGroupBuilder
from pydantic import BaseModel

from greetbot.services.placeholders import apply_user_info
from greetbot.types.extra.file import Base64File
from greetbot.types.media import MediaFile, MediaDataType


class DatabaseMessage(BaseModel):
    caption: str | None = None
    media_files: list[MediaFile]

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
                media_files.append(MediaFile(data_type=MediaDataType.DOCUMENT, base64=Base64File.from_bytes(data_bytes),
                                             file_name=message.document.file_name or "file.txt"))

            if caption is None:
                caption = message.caption or message.text

        return cls(caption=caption, media_files=media_files)

    async def send_as_aiogram_message(self, bot: Bot, chat_id: int, user: User) -> None:
        if len(self.media_files) == 0 and self.caption is not None:
            await bot.send_message(chat_id=chat_id, text=apply_user_info(user, self.caption) or "")
            return
        elif len(self.media_files) > 0:
            media_group = MediaGroupBuilder(caption=apply_user_info(user, self.caption))
            for media in self.media_files:
                file = BufferedInputFile(file=media.base64.to_bytes(), filename=media.file_name or "file")

                media_group.add(type=media.data_type.value, media=file, has_spoiler=media.in_spoiler)  # type: ignore

            await bot.send_media_group(chat_id, media=media_group.build())

    @property
    def settings_report(self) -> str:
        output = ""
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

        return output.strip()

