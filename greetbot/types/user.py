from datetime import datetime

from beanie import Document
from pydantic import Field


class ChannelUser(Document):
    user_id: int
    channel_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
