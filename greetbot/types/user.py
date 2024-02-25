from datetime import datetime
from typing import Self

from beanie import Document
from pydantic import Field, BaseModel


class ChannelUserID(BaseModel):
    user_id: int
    channel_id: int


class User(Document):
    id: ChannelUserID  # type: ignore
    is_blocked: bool = False
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

    @classmethod
    async def get_by_id(cls, user_id: int, channel_id) -> Self | None:
        return await cls.get(ChannelUserID(user_id=user_id, channel_id=channel_id))
