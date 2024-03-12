from pydantic import BaseModel

from greetbot.types.message import DatabaseMessage


class AnswerVariant(BaseModel):
    answer_text: str
    reply_messages: list[DatabaseMessage] = []
