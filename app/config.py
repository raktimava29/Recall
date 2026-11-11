from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    tavily_api_key: str = ""
    database_path: str = "./data/recall.db"
    max_context_messages: int = 10
    search_timeout_seconds: float = 8.0
    local_timezone: str = "UTC"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
