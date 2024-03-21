from datetime import datetime, timedelta

from beanie import Document
from pydantic import Field

from greetbot.types.message import DatabaseMessage, CopyMessage
from greetbot.types.survey import AnswerVariant


class Greeting(DatabaseMessage, Document):
    is_enabled: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    is_survey: bool = False
    delete_survey_after_answer: bool = True
    survey_answer_variants: list[AnswerVariant] = []

    class Settings:
        name = "greeting_messages"
        cache_expiration_time = timedelta(seconds=10)


class GreetingCopy(CopyMessage, Document):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "greeting_copy_messages"
