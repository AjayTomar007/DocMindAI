from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.llm_service import generate_answer
from app.services.search_service import semantic_search

NO_CONTEXT_ANSWER = "I couldn't find anything relevant in your documents yet. Try uploading one first."


@dataclass
class RagResult:
    answer: str
    sources: list[DocumentChunk]


def answer_question(db: Session, query: str) -> RagResult:
    chunks = semantic_search(db, query)
    if not chunks:
        return RagResult(answer=NO_CONTEXT_ANSWER, sources=[])

    answer = generate_answer(query, [chunk.content for chunk in chunks])
    return RagResult(answer=answer, sources=chunks)
