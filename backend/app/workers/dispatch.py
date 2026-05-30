from datetime import datetime

from app.services.workflow_execution_service import StepExecutionResult
from app.workers.celery_app import EMAIL_QUEUE, WORKFLOW_QUEUE


def dispatch_after_step(*, user_id: str, result: StepExecutionResult) -> None:
    """Enqueue the next Celery job based on workflow run state after a step."""
    from app.workers.workflow_worker import execute_workflow_step_task, resume_workflow_task

    if result.status == "completed" or result.action == "completed":
        return

    if result.status == "waiting" and result.next_execution_at is not None:
        resume_workflow_task.apply_async(
            args=[user_id, result.workflow_run_id],
            queue=WORKFLOW_QUEUE,
            eta=_as_utc_naive(result.next_execution_at),
        )
        return

    if result.status == "queued":
        execute_workflow_step_task.apply_async(
            args=[user_id, result.workflow_run_id],
            queue=WORKFLOW_QUEUE,
        )


def enqueue_send_email(*, user_id: str, workflow_run_id: str) -> None:
    from app.workers.email_worker import send_email_task

    send_email_task.apply_async(
        args=[user_id, workflow_run_id],
        queue=EMAIL_QUEUE,
    )


def _as_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.replace(tzinfo=None)
