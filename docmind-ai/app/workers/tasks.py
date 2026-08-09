import uuid
from pathlib import Path

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.chunking_service import chunk_text
from app.services.embedding_service import embed_texts
from app.services.pdf_service import extract_text
from app.workers.celery_app import celery_app


@celery_app.task(name="extract_text_task")
def extract_text_task(document_id: str) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, uuid.UUID(document_id))
        if document is None:
            return

        document.status = "extracting"
        db.commit()

        try:
            text = extract_text(Path(document.filepath))
        except Exception:
            document.status = "extraction_failed"
            db.commit()
            return

        document.extracted_text = text
        document.status = "extracted" if text else "no_text_found"
        db.commit()
    finally:
        db.close()

    if text:
        generate_embeddings_task.delay(document_id)


@celery_app.task(name="generate_embeddings_task")
def generate_embeddings_task(document_id: str) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, uuid.UUID(document_id))
        if document is None or not document.extracted_text:
            return

        document.status = "embedding"
        db.commit()

        try:
            chunks = chunk_text(document.extracted_text)
            embeddings = embed_texts(chunks)
            for index, (content, embedding) in enumerate(zip(chunks, embeddings)):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        content=content,
                        embedding=embedding,
                    )
                )
            document.status = "processed"
            db.commit()
        except Exception:
            db.rollback()
            document.status = "embedding_failed"
            db.commit()
    finally:
        db.close()
