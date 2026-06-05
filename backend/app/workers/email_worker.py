from celery.exceptions import MaxRetriesExceededError
from fastapi import HTTPException

from app.core.logger import get_logger
from app.providers.email.base import EmailProviderError
from app.services.workflow_execution_service import workflow_execution_service
from app.workers.async_runner import run_async, with_database
from app.workers.celery_app import EMAIL_QUEUE, RETRY_QUEUE, celery_app
from app.workers.dispatch import dispatch_after_step

logger = get_logger(__name__)


async def _run_send_email(*, user_id: str, workflow_run_id: str) -> None:
    try:
        result = await workflow_execution_service.execute_step(
            workflow_run_id,
            user_id=user_id,
        )
    except HTTPException:
        raise
    except EmailProviderError as exc:
        raise RuntimeError(str(exc)) from exc

    dispatch_after_step(user_id=user_id, result=result)


@celery_app.task(
    bind=True,
    name="app.workers.email_worker.send_email_task",
    max_retries=3,
    default_retry_delay=300,
)
def send_email_task(self, user_id: str, workflow_run_id: str) -> None:
    try:
        run_async(
            with_database(
                lambda: _run_send_email(
                    user_id=user_id,
                    workflow_run_id=workflow_run_id,
                ),
            ),
        )
        logger.info(
            "send_email_task_completed",
            user_id=user_id,
            workflow_run_id=workflow_run_id,
        )
    except Exception as exc:
        logger.exception(
            "send_email_task_failed",
            user_id=user_id,
            workflow_run_id=workflow_run_id,
        )
        retry_queue = RETRY_QUEUE if self.request.retries > 0 else EMAIL_QUEUE
        try:
            raise self.retry(exc=exc, queue=retry_queue) from exc
        except MaxRetriesExceededError:
            raise
