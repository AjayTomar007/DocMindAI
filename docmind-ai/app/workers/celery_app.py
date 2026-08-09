from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "docmind",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.task_track_started = True
