from fastapi import HTTPException, status

from app.repositories.workflow_repository import WorkflowRecord, workflow_repository
from app.services.workflow_run_queue_service import workflow_run_queue_service

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "active": {"paused"},
    "paused": {"active"},
}


class WorkflowStatusService:
    async def update_status(
        self,
        *,
        user_id: str,
        workflow_id: str,
        new_status: str,
    ) -> WorkflowRecord:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        allowed = _ALLOWED_TRANSITIONS.get(record.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot change workflow status from '{record.status}' to '{new_status}'. "
                    "Use the workflow builder to activate draft campaigns."
                ),
            )

        updated = await workflow_repository.update_status(
            user_id=user_id,
            workflow_id=workflow_id,
            status=new_status,
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        runs_enqueued = 0
        if new_status == "active":
            runs_enqueued = await workflow_run_queue_service.requeue_workflow_runs(
                user_id=user_id,
                workflow_id=workflow_id,
                require_active=True,
            )

        return updated, runs_enqueued


workflow_status_service = WorkflowStatusService()
