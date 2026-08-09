from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.db.session import get_db
from app.services.search_service import semantic_search

router = APIRouter()


@router.post("/chat/message")
def send_message(request: Request, db: Session = Depends(get_db), message: str = Form(...)):
    try:
        results = semantic_search(db, message)
        error = None
    except Exception:
        results = []
        error = "Search is temporarily unavailable. Please try again."

    return templates.TemplateResponse(
        request,
        "partials/chat_results.html",
        {"query": message, "results": results, "error": error},
    )
