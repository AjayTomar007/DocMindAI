import logging
import uuid
from pathlib import Path

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.chunking_service import chunk_text
from app.services.embedding_service import embed_texts
from app.services.pdf_service import extract_text
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="extract_text_task")
def extract_text_task(document_id: str) -> None:
    logger.info("Starting text extraction for document %s", document_id)
    db = SessionLocal()
    try:
        document = db.get(Document, uuid.UUID(document_id))
        if document is None:
            logger.warning("Document %s not found, skipping extraction", document_id)
            return

        document.status = "extracting"
        db.commit()

        try:
            text = extract_text(Path(document.filepath))
        except Exception:
            logger.exception("Text extraction failed for document %s", document_id)
            document.status = "extraction_failed"
            db.commit()
            return

        document.extracted_text = text
        document.status = "extracted" if text else "no_text_found"
        db.commit()
        logger.info("Extraction finished for document %s (status=%s)", document_id, document.status)
    finally:
        db.close()

    if text:
        generate_embeddings_task.delay(document_id)


@celery_app.task(name="generate_embeddings_task")
def generate_embeddings_task(document_id: str) -> None:
    logger.info("Starting chunking + embedding for document %s", document_id)
    db = SessionLocal()
    try:
        document = db.get(Document, uuid.UUID(document_id))
        if document is None or not document.extracted_text:
            logger.warning("Document %s not found or has no text, skipping embedding", document_id)
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
            logger.info("Embedded %d chunks for document %s", len(chunks), document_id)
        except Exception:
            logger.exception("Embedding failed for document %s", document_id)
            db.rollback()
            document.status = "embedding_failed"
            db.commit()
    finally:
        db.close()
