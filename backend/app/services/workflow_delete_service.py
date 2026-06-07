from fastapi import HTTPException, status

from app.core.database import get_database
from app.models.campaign import Campaign
from app.models.workflow_version import WorkflowVersion
from app.repositories.workflow_repository import workflow_repository

_WORKFLOW_SCOPED_COLLECTIONS = (
    "workflow_runs",
    "executions",
    "webhook_events",
    "analytics",
    "email_messages",
    "inbound_replies",
    "tool_executions",
    "email_templates",
    "email_events",
)


class WorkflowDeleteService:
    async def delete_workflow(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> None:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        db = get_database()

        await db["conversations"].delete_many(
            {"user_id": user_id, "workflow_id": workflow_id},
        )

        workflow_scope = {"$or": [{"workflow_id": workflow_id}, {"campaign_id": workflow_id}]}
        await db["leads"].delete_many(workflow_scope)
        await db["conversation_threads"].delete_many(workflow_scope)

        for collection in _WORKFLOW_SCOPED_COLLECTIONS:
            await db[collection].delete_many({"workflow_id": workflow_id})

        await WorkflowVersion.find(WorkflowVersion.workflow_id == workflow_id).delete()
        await Campaign.find(
            Campaign.user_id == user_id,
            Campaign.workflow_id == workflow_id,
        ).delete()

        await workflow_repository.delete(user_id=user_id, workflow_id=workflow_id)


workflow_delete_service = WorkflowDeleteService()
