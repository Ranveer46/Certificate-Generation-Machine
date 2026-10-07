"""
Celery application instance.

Broker  : Redis (list 0)
Backend : Redis (list 1) — stores task results
"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "certificate_generator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Retry policy for transient failures
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
