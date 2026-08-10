from collections.abc import Iterator

from app.core.config import settings
from app.services.openai_client import get_client

SYSTEM_PROMPT = (
    "Answer the user's question using only the provided context. "
    "If the answer isn't in the context, say you don't know — do not make things up."
)


def _build_messages(query: str, context_chunks: list[str]) -> list[dict]:
    context = "\n\n---\n\n".join(context_chunks)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
    ]


def generate_answer(query: str, context_chunks: list[str]) -> str:
    response = get_client().chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL, messages=_build_messages(query, context_chunks)
    )
    return response.choices[0].message.content or ""


def stream_answer(query: str, context_chunks: list[str]) -> Iterator[str]:
    stream = get_client().chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL, messages=_build_messages(query, context_chunks), stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
