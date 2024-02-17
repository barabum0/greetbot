from enum import StrEnum

from beanie import Document
from pydantic import BaseModel

from greetbot.types.extra.file import Base64File


class MediaDataType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class MediaFile(BaseModel):
    data_type: MediaDataType
    base64: Base64File


class Greeting(BaseModel):
    caption: str | None = None


class BotConfig(Document):
    id: int = 0  # type: ignore
    greetings: list[Greeting] = []

    class Settings:
        name = "bot_config"