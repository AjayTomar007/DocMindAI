from fastapi import APIRouter, Request

from app.core.templates import templates

router = APIRouter()


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"active": "home"})


@router.get("/upload")
def upload_page(request: Request):
    return templates.TemplateResponse(request, "upload.html", {"active": "upload"})


@router.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {"active": "chat"})


@router.get("/history")
def history_page(request: Request):
    return templates.TemplateResponse(request, "history.html", {"active": "history"})
