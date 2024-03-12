import asyncio
import textwrap
from datetime import datetime
from html import escape

from aiogram import Bot
from aiogram.types import BufferedInputFile, User
from aiogram.utils.media_group import MediaGroupBuilder
from beanie import Document
from pydantic import Field

from greetbot.services.placeholders import apply_user_info
from greetbot.types.extra.file import Base64File
from greetbot.types.media import MediaDataType
from greetbot.types.message import DatabaseMessage
from greetbot.types.settings import settings


class Greeting(DatabaseMessage, Document):
    is_enabled: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


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