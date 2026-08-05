import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.services.pdf_service import extract_text

ALLOWED_CONTENT_TYPE = "application/pdf"
CHUNK_SIZE = 1024 * 1024  # 1 MB


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
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        text = extract_text(Path(document.filepath))
        document.extracted_text = text
        document.status = "processed" if text else "no_text_found"
    except Exception:
        document.status = "extraction_failed"
    db.commit()
    db.refresh(document)

    return document


def list_documents(db: Session) -> list[Document]:
    stmt = select(Document).order_by(Document.created_at.desc())
    return list(db.scalars(stmt))
