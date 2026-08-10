import logging
import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.workers.tasks import extract_text_task

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPE = "application/pdf"
CHUNK_SIZE = 1024 * 1024  # 1 MB
TERMINAL_STATUSES = {"processed", "no_text_found", "extraction_failed", "embedding_failed"}


class InvalidFileType(Exception):
    pass


async def save_upload(db: Session, upload_file: UploadFile) -> Document:
    if upload_file.content_type != ALLOWED_CONTENT_TYPE:
        raise InvalidFileType(f"Unsupported file type: {upload_file.content_type}")

    stored_name = f"{uuid.uuid4()}.pdf"
    destination = settings.STORAGE_DIR / stored_name

    size_bytes = 0
    with destination.open("wb") as buffer:
        while chunk := await upload_file.read(CHUNK_SIZE):
            size_bytes += len(chunk)
            buffer.write(chunk)

    document = Document(
        filename=upload_file.filename or stored_name,
        filepath=str(destination),
        content_type=upload_file.content_type,
        size_bytes=size_bytes,
        status="queued",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    logger.info("Received upload %s (%s, %d bytes)", document.id, document.filename, size_bytes)
    extract_text_task.delay(str(document.id))

    return document


def list_documents(db: Session) -> list[Document]:
    stmt = select(Document).order_by(Document.created_at.desc())
    return list(db.scalars(stmt))


def all_processed(documents: list[Document]) -> bool:
    return all(doc.status in TERMINAL_STATUSES for doc in documents)
