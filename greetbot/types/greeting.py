from datetime import datetime

from beanie import Document
from pydantic import Field

from greetbot.types.message import DatabaseMessage
from greetbot.types.survey import AnswerVariant


class Greeting(DatabaseMessage, Document):
    is_enabled: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    is_survey: bool = False
    survey_answer_variants: list[AnswerVariant] = []

    class Settings:
        name = "greeting_messages"
