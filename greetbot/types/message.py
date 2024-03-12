from typing import Self

from aiogram import Bot
from aiogram.types import Message
from pydantic import BaseModel

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
