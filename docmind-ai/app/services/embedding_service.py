from app.core.config import settings
from app.services.openai_client import get_client


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = get_client().embeddings.create(model=settings.OPENAI_EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]
