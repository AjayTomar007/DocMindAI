from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.pages import router as pages_router

app = FastAPI(title="DocMind AI")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages_router)
