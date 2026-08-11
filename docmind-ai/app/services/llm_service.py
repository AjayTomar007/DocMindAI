from collections.abc import Iterator

from google.genai import types

from app.core.config import settings
from app.services.gemini_client import get_client

SYSTEM_PROMPT = (
    "Answer the user's question using only the provided context. "
    "If the answer isn't in the context, say you don't know — do not make things up."
)


def _build_prompt(query: str, context_chunks: list[str]) -> tuple[str, types.GenerateContentConfig]:
    context = "\n\n---\n\n".join(context_chunks)
    contents = f"Context:\n{context}\n\nQuestion: {query}"
    config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    return contents, config


def generate_answer(query: str, context_chunks: list[str]) -> str:
    contents, config = _build_prompt(query, context_chunks)
    response = get_client().models.generate_content(
        model=settings.GEMINI_CHAT_MODEL, contents=contents, config=config
    )
    return response.text or ""


def stream_answer(query: str, context_chunks: list[str]) -> Iterator[str]:
    contents, config = _build_prompt(query, context_chunks)
    stream = get_client().models.generate_content_stream(
        model=settings.GEMINI_CHAT_MODEL, contents=contents, config=config
    )
    for chunk in stream:
        if chunk.text:
            yield chunk.text
