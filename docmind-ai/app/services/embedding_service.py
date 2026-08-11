from google.genai import types

from app.core.config import settings
from app.services.gemini_client import get_client


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = get_client().models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(output_dimensionality=settings.EMBEDDING_DIM),
    )
    return [embedding.values for embedding in response.embeddings]
