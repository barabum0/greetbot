from random import randint

from pydantic import BaseModel, Field

from greetbot.types.message import DatabaseMessage


class AnswerVariant(BaseModel):
    answer_text: str
    answer_id: str = Field(default_factory=lambda: str(randint(0, 1000)))
    reply_messages: list[DatabaseMessage] = []
