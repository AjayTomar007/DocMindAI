from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://docmind:docmind@localhost:5432/docmind"
    STORAGE_DIR: Path = Path("storage/uploads")


settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
