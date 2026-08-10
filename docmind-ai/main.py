import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.pages import router as pages_router
from app.core.logging import configure_logging
from app.core.templates import templates

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="DocMind AI")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(health_router)


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if _is_htmx(request):
        return HTMLResponse(
            content=f'<div class="alert alert-danger mb-0">{exc.detail}</div>', status_code=exc.status_code
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {"active": None, "status_code": exc.status_code, "message": exc.detail},
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    message = "Something went wrong on our end."
    if _is_htmx(request):
        return HTMLResponse(content=f'<div class="alert alert-danger mb-0">{message}</div>', status_code=500)
    return templates.TemplateResponse(
        request, "error.html", {"active": None, "status_code": 500, "message": message}, status_code=500
    )
