from enum import StrEnum

from pydantic import BaseModel

from greetbot.types.extra.file import Base64File


class MediaDataType(StrEnum):
    IMAGE = "photo"
    VIDEO = "video"
    DOCUMENT = "document"


class MediaFile(BaseModel):
    data_type: MediaDataType
    base64: Base64File
    thumbnail_base64: Base64File | None = None
    in_spoiler: bool = False
    file_name: str | None = None