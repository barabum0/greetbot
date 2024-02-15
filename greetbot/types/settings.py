from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_prefix="greetbot__", env_nested_delimiter="__")

    bot_token: str


settings = Settings()  # type: ignore[call-arg]
