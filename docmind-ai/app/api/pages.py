from fastapi import APIRouter, Request

from app.core.templates import templates

router = APIRouter()


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"active": "home"})
