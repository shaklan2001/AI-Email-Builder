from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.langgraph.state import ConversationState
from app.repositories.conversation_repository import conversation_repository
from app.repositories.execution_repository import execution_repository
from app.repositories.workflow_repository import workflow_repository
from app.schemas.requests import ActivateWorkflowData
from app.schemas.workflow import WorkflowDefinition
from app.services.conversation_stage import _has_workflow_steps
from app.services.email_service import EmailService
from app.services.workflow_execution_service import workflow_execution_service
from app.services.workflow_structure import normalize_for_execution
from app.services.workflow_version_service import workflow_version_service
from app.workers.celery_app import WORKFLOW_QUEUE
from app.workers.workflow_worker import execute_workflow_step_task


def _recipient_emails_from_state(state: ConversationState) -> list[str]:
    emails: list[str] = []
    stored = state.get("recipients")
    if not isinstance(stored, list):
        return emails
    for item in stored:
        if isinstance(item, str) and item.strip():
            emails.append(item.strip())
        elif isinstance(item, dict):
            email = item.get("email")
            if isinstance(email, str) and email.strip():
                emails.append(email.strip())
    return emails


def _merge_recipients_into_workflow(
    workflow_raw: dict[str, object],
    recipient_emails: list[str],
) -> dict[str, object]:
    if not recipient_emails:
        return workflow_raw
    merged = dict(workflow_raw)
    merged["recipient_emails"] = recipient_emails
    return merged


class WorkflowActivationService:
    async def _load_workflow_definition_raw(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> dict[str, object]:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is not None and isinstance(record.workflow_definition, dict):
            return record.workflow_definition

        state = await conversation_repository.get_campaign_state(user_id, workflow_id)
        if state is not None:
            raw_workflow = state.get("workflow")
            if isinstance(raw_workflow, dict):
                return raw_workflow

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    async def _resolve_workflow_for_activation(
        self,
        *,
        user_id: str,
        workflow_id: str,
        state: ConversationState,
    ) -> dict[str, object]:
        workflow_raw = await self._load_workflow_definition_raw(
            user_id=user_id,
            workflow_id=workflow_id,
        )
        recipients = EmailService._extract_recipients(workflow_raw)
        if not recipients:
            recipients = _recipient_emails_from_state(state)
        if recipients:
            workflow_raw = _merge_recipients_into_workflow(workflow_raw, recipients)
            await workflow_repository.upsert_workflow_definition(
                user_id=user_id,
                workflow_id=workflow_id,
                workflow_definition=workflow_raw,
            )
        return workflow_raw

    async def activate(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> ActivateWorkflowData:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        if record.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow is already active",
            )

        allowed_statuses = {"draft", "awaiting_activation"}
        if record.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow cannot be activated from status '{record.status}'",
            )

        state = await conversation_repository.get_conversation_state(
            user_id,
            workflow_id,
        )
        if state is None or state.get("review_status") != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workflow must be approved on the review screen before activation",
            )
        if not _has_workflow_steps(state.get("workflow")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow has no generated steps",
            )

        workflow_raw = await self._resolve_workflow_for_activation(
            user_id=user_id,
            workflow_id=workflow_id,
            state=state,
        )
        steps = workflow_raw.get("steps")
        if not isinstance(steps, list) or not steps:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow has no steps",
            )

        raw_recipients = EmailService._extract_recipients(workflow_raw)
        if not raw_recipients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow has no recipients",
            )
        recipients = EmailService.validate_recipients(raw_recipients)

        definition = normalize_for_execution(
            WorkflowDefinition.model_validate(workflow_raw),
        )
        first_step_id = definition.steps[0].id

        version_doc = await workflow_version_service.create_snapshot(
            workflow_id=workflow_id,
            workflow_raw=workflow_raw,
        )
        activated_at = datetime.now(UTC)

        updated = await workflow_repository.activate(
            user_id=user_id,
            workflow_id=workflow_id,
            active_version=version_doc.version,
            workflow_definition=workflow_raw,
            activated_at=activated_at,
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        runs_queued = 0
        for recipient_email in recipients:
            existing_execution = await execution_repository.find_by_workflow_and_lead(
                workflow_id,
                recipient_email,
            )
            if existing_execution is None:
                await execution_repository.create(
                    workflow_id=workflow_id,
                    lead_id=recipient_email,
                    current_step_id=first_step_id,
                    workflow_version=version_doc.version,
                    next_execution_at=activated_at,
                )

            run = await workflow_execution_service.create_run(
                user_id=user_id,
                workflow_id=workflow_id,
                recipient_id=recipient_email,
            )
            execute_workflow_step_task.apply_async(
                args=[user_id, run.id],
                queue=WORKFLOW_QUEUE,
            )
            runs_queued += 1

        return ActivateWorkflowData(
            workflow_id=workflow_id,
            status="active",
            active_version=version_doc.version,
            activated_at=activated_at.isoformat(),
            executions_created=runs_queued,
            runs_queued=runs_queued,
            message="Workflow activated. Emails will begin sending shortly.",
        )


workflow_activation_service = WorkflowActivationService()
