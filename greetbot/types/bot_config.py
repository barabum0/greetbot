import asyncio
import textwrap
from datetime import datetime
from enum import StrEnum
from html import escape

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from beanie import Document
from pydantic import BaseModel, Field

from greetbot.types.extra.file import Base64File
from greetbot.types.settings import settings


class MediaDataType(StrEnum):
    IMAGE = "photo"
    VIDEO = "video"
    DOCUMENT = "document"


class MediaFile(BaseModel):
    data_type: MediaDataType
    base64: Base64File
    in_spoiler: bool = False
    file_name: str | None = None


class Greeting(Document):
    caption: str | None = None
    media_files: list[MediaFile]

    is_enabled: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    async def send_as_aiogram_message(self, bot: Bot, chat_id: int) -> None:
        if len(self.media_files) == 0 and self.caption is not None:
            await bot.send_message(chat_id=chat_id, text=self.caption)
            return
        elif len(self.media_files) > 0:
            media_group = MediaGroupBuilder(caption=self.caption)
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

    class Settings:
        name = "greeting_messages"


if __name__ == '__main__':
    bot = Bot(token=settings.bot_token)
    test_greeting = Greeting(
        caption="testcaption",
        media_files=[
            MediaFile(data_type=MediaDataType.IMAGE, base64=Base64File.from_bytes(open("/Users/roman/Downloads/7ee68cf9-9c29-4021-beb4-4c781a0df501.png", "rb").read())),
            MediaFile(data_type=MediaDataType.IMAGE, base64=Base64File.from_bytes(
                open("/Users/roman/Downloads/50_2196_post_media_Zq5V.jpg", "rb").read()), in_spoiler=True)
        ]
    )
    asyncio.run(test_greeting.send_as_aiogram_message(bot, 733876760))