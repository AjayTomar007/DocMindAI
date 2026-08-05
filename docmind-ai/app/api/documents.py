from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.db.session import get_db
from app.services.document_service import InvalidFileType, list_documents, save_upload

router = APIRouter()


@router.get("/upload")
def upload_page(request: Request, db: Session = Depends(get_db)):
    documents = list_documents(db)
    return templates.TemplateResponse(
        request, "upload.html", {"active": "upload", "documents": documents}
    )


@router.post("/upload")
async def upload_document(db: Session = Depends(get_db), file: UploadFile = File(...)):
    try:
        await save_upload(db, file)
    except InvalidFileType:
        return RedirectResponse(url="/upload?error=invalid_type", status_code=303)
    return RedirectResponse(url="/upload", status_code=303)
