from pydantic import BaseModel

from greetbot.types.media import MediaFile


class DatabaseMessage(BaseModel):
    caption: str | None = None
    media_files: list[MediaFile]