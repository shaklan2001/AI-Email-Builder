from celery.exceptions import MaxRetriesExceededError
from fastapi import HTTPException

from app.core.logger import get_logger
from app.workers.async_runner import run_async, with_database
from app.workers.celery_app import WORKFLOW_QUEUE, celery_app
from app.workers.workflow_runner import run_execute_workflow_step, run_resume_workflow

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.workers.workflow_worker.execute_workflow_step_task",
    max_retries=3,
    default_retry_delay=60,
)
def execute_workflow_step_task(self, user_id: str, workflow_run_id: str) -> None:
    try:
        run_async(
            with_database(
                lambda: run_execute_workflow_step(
                    user_id=user_id,
                    workflow_run_id=workflow_run_id,
                ),
            ),
        )
        logger.info(
            "workflow_step_task_completed",
            user_id=user_id,
            workflow_run_id=workflow_run_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "workflow_step_task_failed",
            user_id=user_id,
            workflow_run_id=workflow_run_id,
        )
        try:
            raise self.retry(exc=exc, queue=WORKFLOW_QUEUE) from exc
        except MaxRetriesExceededError:
            raise


@celery_app.task(
    bind=True,
    name="app.workers.workflow_worker.resume_workflow_task",
    max_retries=3,
    default_retry_delay=60,
)
def resume_workflow_task(self, user_id: str, workflow_run_id: str) -> None:
    try:
        run_async(
            with_database(
                lambda: run_resume_workflow(
                    user_id=user_id,
                    workflow_run_id=workflow_run_id,
                ),
            ),
        )
        logger.info(
            "resume_workflow_task_completed",
            user_id=user_id,
            workflow_run_id=workflow_run_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "resume_workflow_task_failed",
            user_id=user_id,
            workflow_run_id=workflow_run_id,
        )
        try:
            raise self.retry(exc=exc, queue=WORKFLOW_QUEUE) from exc
        except MaxRetriesExceededError:
            raise
