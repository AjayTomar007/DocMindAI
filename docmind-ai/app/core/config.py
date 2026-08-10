from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://docmind:docmind@localhost:5432/docmind"
    STORAGE_DIR: Path = Path("storage/uploads")

    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/1"

    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    EMBEDDING_DIM: int = 1536

    REDIS_URL: str = "redis://127.0.0.1:6379/2"
    RATE_LIMIT_PER_MINUTE: int = 20


settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
