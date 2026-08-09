from functools import lru_cache

from openai import OpenAI

from app.core.config import settings


@lru_cache
def _get_client() -> OpenAI:
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = _get_client().embeddings.create(model=settings.OPENAI_EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]
