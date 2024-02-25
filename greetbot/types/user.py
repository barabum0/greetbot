from datetime import datetime

from beanie import Document
from pydantic import Field


class User(Document):
    id: int  # type: ignore
    is_blocked: bool = False
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
