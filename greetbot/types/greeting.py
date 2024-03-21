from datetime import datetime, timedelta
from typing import Optional, OrderedDict

from beanie import Document, WriteRules
from beanie.odm.documents import DocType
from pydantic import Field
from pymongo.client_session import ClientSession

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

    @classmethod
    async def save(
        self: DocType,
        session: Optional[ClientSession] = None,
        link_rule: WriteRules = WriteRules.DO_NOTHING,
        ignore_revision: bool = False,
        **kwargs,
    ) -> None:
        await self.save(session, link_rule, ignore_revision, **kwargs)
        self._cache.cache = OrderedDict()


class GreetingCopy(CopyMessage, Document):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "greeting_copy_messages"
