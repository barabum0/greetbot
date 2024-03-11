from typing import Annotated

from pydantic import MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_prefix="greetbot__", env_nested_delimiter="__")

    mongo_url: Annotated[str, MongoDsn]
    mongo_db_name: str
    bot_token: str
    show_credits: bool = True
    require_request_confirmation: bool = False
    request_confirmation_message_text: str = "Вступить в канал <b>{{ channel_name }}</b>?"
    request_confirmation_button_text: str = "✅ Вступить"


settings = Settings()  # type: ignore[call-arg]
