from datetime import datetime

from beanie import Document
from pydantic import Field

from greetbot.types.message import DatabaseMessage


class Greeting(DatabaseMessage, Document):
    is_enabled: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "greeting_messages"
