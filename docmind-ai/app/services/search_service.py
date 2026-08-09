from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import embed_texts

DEFAULT_TOP_K = 5


def semantic_search(db: Session, query: str, top_k: int = DEFAULT_TOP_K) -> list[DocumentChunk]:
    query_embedding = embed_texts([query])[0]
    stmt = (
        select(DocumentChunk)
        .options(selectinload(DocumentChunk.document))
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return list(db.scalars(stmt))
