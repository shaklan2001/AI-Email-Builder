from celery import Celery
from kombu import Queue

from app.core.config import settings

WORKFLOW_QUEUE = "workflow_queue"
EMAIL_QUEUE = "email_queue"
RETRY_QUEUE = "retry_queue"

celery_app = Celery(
    "email_workflow_builder",
    broker=settings.celery_broker,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.workflow_worker",
        "app.workers.email_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_queues=(
        Queue(WORKFLOW_QUEUE),
        Queue(EMAIL_QUEUE),
        Queue(RETRY_QUEUE),
    ),
    task_routes={
        "app.workers.workflow_worker.execute_workflow_step_task": {"queue": WORKFLOW_QUEUE},
        "app.workers.workflow_worker.resume_workflow_task": {"queue": WORKFLOW_QUEUE},
        "app.workers.email_worker.send_email_task": {"queue": EMAIL_QUEUE},
    },
    task_default_queue=WORKFLOW_QUEUE,
)
