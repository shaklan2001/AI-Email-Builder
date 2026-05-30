from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.repositories.workflow_repository import workflow_repository
from app.repositories.workflow_run_repository import workflow_run_repository
from app.workers.celery_app import WORKFLOW_QUEUE
from app.workers.dispatch import _as_utc_naive


class WorkflowRunQueueService:
    async def requeue_workflow_runs(
        self,
        *,
        user_id: str,
        workflow_id: str,
        require_active: bool = True,
    ) -> int:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )
        if require_active and record.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow must be active to queue email runs",
            )

        from app.workers.workflow_worker import (
            execute_workflow_step_task,
            resume_workflow_task,
        )

        runs = await workflow_run_repository.find_pending_by_workflow(workflow_id)
        now = datetime.now(UTC)
        enqueued = 0

        for run in runs:
            if run.status in ("queued", "running"):
                execute_workflow_step_task.apply_async(
                    args=[user_id, run.id],
                    queue=WORKFLOW_QUEUE,
                )
                enqueued += 1
                continue

            if run.status == "waiting":
                kwargs: dict = {
                    "args": [user_id, run.id],
                    "queue": WORKFLOW_QUEUE,
                }
                if run.next_execution_at is not None and run.next_execution_at > now:
                    kwargs["eta"] = _as_utc_naive(run.next_execution_at)
                resume_workflow_task.apply_async(**kwargs)
                enqueued += 1

        return enqueued


workflow_run_queue_service = WorkflowRunQueueService()
