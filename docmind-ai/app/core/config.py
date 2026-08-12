from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://docmind:docmind@localhost:5432/docmind"
    STORAGE_DIR: Path = Path("storage/uploads")

    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/1"

    GEMINI_API_KEY: str = ""
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_CHAT_MODEL: str = "gemini-3.6-flash"
    EMBEDDING_DIM: int = 1536

    REDIS_URL: str = "redis://127.0.0.1:6379/2"
    RATE_LIMIT_PER_MINUTE: int = 20

    @field_validator("DATABASE_URL")
    @classmethod
    def _use_psycopg_driver(cls, value: str) -> str:
        # Managed Postgres providers (Render, Heroku, etc.) hand back a plain
        # postgres:// or postgresql:// URL. SQLAlchemy defaults that scheme to
        # psycopg2, which isn't installed here — we use psycopg (v3) everywhere.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix) and not value.startswith("postgresql+psycopg://"):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value


settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
