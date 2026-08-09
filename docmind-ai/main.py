from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.pages import router as pages_router

app = FastAPI(title="DocMind AI")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages_router)
app.include_router(documents_router)
app.include_router(chat_router)
