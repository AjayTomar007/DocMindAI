from functools import lru_cache

from openai import OpenAI

from app.core.config import settings


@lru_cache
def get_client() -> OpenAI:
    return OpenAI(api_key=settings.OPENAI_API_KEY)
