from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.models.workflow_run import WorkflowRun, WorkflowRunStatus
from app.providers.email.base import EmailProviderError
from app.services.email_service import EmailService, email_service
from app.repositories.conversation_repository import conversation_repository
from app.repositories.workflow_repository import workflow_repository
from app.repositories.workflow_run_repository import WorkflowRunRepository, workflow_run_repository
from app.schemas.email import EmailBodyVersion
from app.schemas.follow_up_delay import FollowUpDelay
from app.schemas.workflow import StepType, WorkflowDefinition, WorkflowStep
from app.services.follow_up_delay import follow_up_delay_to_timedelta
from app.services.workflow_structure import normalize_for_execution
from app.services.workflow_version_service import workflow_version_service
from app.services.analytics_service import AnalyticsService, analytics_service


class StepExecutionResult(BaseModel):
    workflow_run_id: str
    step_id: str
    step_type: StepType
    action: Literal["sent_email", "scheduled_wait", "evaluated_condition", "completed", "waiting"]
    status: WorkflowRunStatus
    next_step_id: str | None = None
    next_execution_at: datetime | None = None
    message_id: str | None = None


class WorkflowExecutionService:
    def __init__(
        self,
        *,
        run_repository: WorkflowRunRepository | None = None,
        email: EmailService | None = None,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._run_repository = run_repository or workflow_run_repository
        self._email_service = email or email_service
        self._analytics_service = analytics or analytics_service

    async def _load_workflow_definition_raw(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> dict[str, object]:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if (
            record is not None
            and record.status == "active"
            and record.active_version is not None
        ):
            frozen = await workflow_version_service.get_definition_dict(
                workflow_id=workflow_id,
                version=record.active_version,
            )
            if frozen is not None:
                return frozen

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

    @staticmethod
    def _step_index(steps: list[WorkflowStep], step_id: str) -> int:
        for index, step in enumerate(steps):
            if step.id == step_id:
                return index
        return -1

    @staticmethod
    def _find_step(steps: list[WorkflowStep], step_id: str) -> WorkflowStep | None:
        for step in steps:
            if step.id == step_id:
                return step
        return None

    @staticmethod
    def _branch_for_condition(condition_result: bool) -> Literal["yes", "no"]:
        return "yes" if condition_result else "no"

    @staticmethod
    def _is_reply_check_step(step: WorkflowStep) -> bool:
        return step.type == "reply_condition" or (
            step.type == "condition" and step.condition == "reply_received"
        )

    @staticmethod
    def _default_reply_check_result(step: WorkflowStep) -> bool | None:
        """After the wait elapses with no inbound reply, take the No branch."""
        if WorkflowExecutionService._is_reply_check_step(step):
            return False
        return None

    def _next_linear_step_id(
        self,
        steps: list[WorkflowStep],
        current_step_id: str,
    ) -> str | None:
        current_index = self._step_index(steps, current_step_id)
        if current_index < 0:
            return None

        for step in steps[current_index + 1 :]:
            if step.branch is None:
                return step.id
        return None

    def _branch_step_id(
        self,
        steps: list[WorkflowStep],
        branch: Literal["yes", "no"],
    ) -> str | None:
        for step in steps:
            if step.branch == branch:
                return step.id
        return None

    @staticmethod
    def _resolve_recipient_email(
        workflow_raw: dict[str, object],
        recipient_id: str,
    ) -> str | None:
        recipient_emails = workflow_raw.get("recipient_emails")
        if isinstance(recipient_emails, list):
            for item in recipient_emails:
                if isinstance(item, str) and item.strip():
                    if item.strip() == recipient_id:
                        return item.strip()

        recipients = workflow_raw.get("recipients")
        if isinstance(recipients, list):
            for item in recipients:
                if isinstance(item, str) and item.strip():
                    if item.strip() == recipient_id:
                        return item.strip()
                elif isinstance(item, dict):
                    item_id = item.get("id")
                    email = item.get("email")
                    if isinstance(email, str) and email.strip():
                        if recipient_id in {str(item_id), email.strip()}:
                            return email.strip()

        if "@" in recipient_id:
            return recipient_id
        return None

    @staticmethod
    def _parse_definition(workflow_raw: dict[str, object]) -> WorkflowDefinition:
        definition = WorkflowDefinition.model_validate(workflow_raw)
        return normalize_for_execution(definition)

    @staticmethod
    def _wait_timedelta(definition: WorkflowDefinition, step: WorkflowStep) -> timedelta:
        if step.value is not None and step.unit is not None:
            return follow_up_delay_to_timedelta(
                FollowUpDelay(value=step.value, unit=step.unit),
            )
        if definition.follow_up_delay is not None:
            return follow_up_delay_to_timedelta(definition.follow_up_delay)
        days = step.days or 1
        return timedelta(days=days)

    @staticmethod
    def _email_body_from_step(step: WorkflowStep) -> EmailBodyVersion | None:
        if step.email is None:
            return None
        return step.email.final_user_version

    async def create_run(
        self,
        *,
        user_id: str,
        workflow_id: str,
        recipient_id: str,
    ) -> WorkflowRun:
        workflow_raw = await self._load_workflow_definition_raw(
            user_id=user_id,
            workflow_id=workflow_id,
        )
        definition = self._parse_definition(workflow_raw)
        if not definition.steps:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow has no steps",
            )

        existing = await self._run_repository.find_by_workflow_and_recipient(
            workflow_id,
            recipient_id,
        )
        if existing is not None:
            return existing

        first_step = definition.steps[0]
        now = datetime.now(UTC)
        return await self._run_repository.create(
            workflow_id=workflow_id,
            recipient_id=recipient_id,
            current_step=first_step.id,
            status="queued",
            next_execution_at=now,
        )

    async def execute_step(
        self,
        workflow_run_id: str,
        *,
        user_id: str,
        condition_result: bool | None = None,
        now: datetime | None = None,
    ) -> StepExecutionResult:
        run = await self._run_repository.get_by_id(workflow_run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow run not found",
            )

        if run.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow run is already completed",
            )

        current_time = now or datetime.now(UTC)
        workflow_raw = await self._load_workflow_definition_raw(
            user_id=user_id,
            workflow_id=run.workflow_id,
        )
        definition = self._parse_definition(workflow_raw)
        steps = definition.steps
        current_step = self._find_step(steps, run.current_step)
        if current_step is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown step: {run.current_step}",
            )

        workflow_record = await workflow_repository.get_by_id(user_id, run.workflow_id)
        if workflow_record is not None and workflow_record.status != "active":
            return StepExecutionResult(
                workflow_run_id=run.id,
                step_id=current_step.id,
                step_type=current_step.type,
                action="waiting",
                status=run.status,
                next_step_id=current_step.id,
                next_execution_at=run.next_execution_at,
            )

        if run.status == "waiting":
            if run.next_execution_at is None or run.next_execution_at > current_time:
                return StepExecutionResult(
                    workflow_run_id=run.id,
                    step_id=current_step.id,
                    step_type=current_step.type,
                    action="waiting",
                    status=run.status,
                    next_step_id=current_step.id,
                    next_execution_at=run.next_execution_at,
                )

            next_step_id = self._next_linear_step_id(steps, current_step.id)
            if next_step_id is None:
                updated = await self._run_repository.update(
                    run.id,
                    status="completed",
                    next_execution_at=None,
                )
                assert updated is not None
                return StepExecutionResult(
                    workflow_run_id=updated.id,
                    step_id=current_step.id,
                    step_type=current_step.type,
                    action="completed",
                    status=updated.status,
                )

            updated = await self._run_repository.update(
                run.id,
                current_step=next_step_id,
                status="queued",
                next_execution_at=current_time,
            )
            assert updated is not None
            next_step = self._find_step(steps, next_step_id)
            assert next_step is not None

            reply_check = self._default_reply_check_result(next_step)
            if reply_check is not None:
                return await self._execute_condition(
                    run=updated,
                    step=next_step,
                    steps=steps,
                    condition_result=reply_check,
                )

            return StepExecutionResult(
                workflow_run_id=updated.id,
                step_id=current_step.id,
                step_type=current_step.type,
                action="scheduled_wait",
                status=updated.status,
                next_step_id=next_step_id,
                next_execution_at=updated.next_execution_at,
            )

        await self._run_repository.update(run.id, status="running")

        if current_step.type == "send_email":
            return await self._execute_send_email(
                run=run,
                step=current_step,
                steps=steps,
                workflow_raw=workflow_raw,
                definition=definition,
            )

        if current_step.type == "wait":
            return await self._execute_wait(
                run=run,
                step=current_step,
                definition=definition,
                now=current_time,
            )

        if current_step.type in ("condition", "reply_condition"):
            return await self._execute_condition(
                run=run,
                step=current_step,
                steps=steps,
                condition_result=condition_result,
            )

        if current_step.type in ("interested_branch", "end"):
            updated = await self._run_repository.update(
                run.id,
                status="completed",
                next_execution_at=None,
            )
            assert updated is not None
            return StepExecutionResult(
                workflow_run_id=updated.id,
                step_id=current_step.id,
                step_type=current_step.type,
                action="completed",
                status=updated.status,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported step type: {current_step.type}",
        )

    async def _execute_send_email(
        self,
        *,
        run: WorkflowRun,
        step: WorkflowStep,
        steps: list[WorkflowStep],
        workflow_raw: dict[str, object],
        definition: WorkflowDefinition,
    ) -> StepExecutionResult:
        body = self._email_body_from_step(step)
        if body is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Step {step.id} has no email content",
            )

        recipient_email = self._resolve_recipient_email(workflow_raw, run.recipient_id)
        if recipient_email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recipient email not found for {run.recipient_id}",
            )

        try:
            send_result = await self._email_service.send_email(
                workflow_id=run.workflow_id,
                lead_id=recipient_email,
                subject=body.subject,
                html_content=body.html_content,
                plain_text_content=body.plain_text_content,
                step_id=step.id,
            )
            message_id = send_result.resend_message_id
        except HTTPException as exc:
            if exc.status_code == status.HTTP_502_BAD_GATEWAY:
                await self._run_repository.update(run.id, status="failed")
            raise
        next_step_id = self._next_linear_step_id(steps, step.id)
        if next_step_id is None:
            updated = await self._run_repository.update(
                run.id,
                status="completed",
                next_execution_at=None,
            )
            assert updated is not None
            return StepExecutionResult(
                workflow_run_id=updated.id,
                step_id=step.id,
                step_type=step.type,
                action="sent_email",
                status=updated.status,
                message_id=message_id,
            )

        next_step = self._find_step(steps, next_step_id)
        assert next_step is not None

        if next_step.type == "wait":
            wait_at = datetime.now(UTC)
            resume_at = wait_at + self._wait_timedelta(definition, next_step)
            updated = await self._run_repository.update(
                run.id,
                current_step=next_step_id,
                status="waiting",
                next_execution_at=resume_at,
            )
            assert updated is not None
            return StepExecutionResult(
                workflow_run_id=updated.id,
                step_id=step.id,
                step_type=step.type,
                action="sent_email",
                status=updated.status,
                next_step_id=next_step_id,
                next_execution_at=resume_at,
                message_id=message_id,
            )

        updated = await self._run_repository.update(
            run.id,
            current_step=next_step_id,
            status="queued",
            next_execution_at=datetime.now(UTC),
        )
        assert updated is not None
        return StepExecutionResult(
            workflow_run_id=updated.id,
            step_id=step.id,
            step_type=step.type,
            action="sent_email",
            status=updated.status,
            next_step_id=next_step_id,
            next_execution_at=updated.next_execution_at,
            message_id=message_id,
        )

    async def _execute_wait(
        self,
        *,
        run: WorkflowRun,
        step: WorkflowStep,
        definition: WorkflowDefinition,
        now: datetime,
    ) -> StepExecutionResult:
        resume_at = now + self._wait_timedelta(definition, step)
        updated = await self._run_repository.update(
            run.id,
            status="waiting",
            next_execution_at=resume_at,
        )
        assert updated is not None
        return StepExecutionResult(
            workflow_run_id=updated.id,
            step_id=step.id,
            step_type=step.type,
            action="scheduled_wait",
            status=updated.status,
            next_step_id=step.id,
            next_execution_at=resume_at,
        )

    async def _execute_condition(
        self,
        *,
        run: WorkflowRun,
        step: WorkflowStep,
        steps: list[WorkflowStep],
        condition_result: bool | None,
    ) -> StepExecutionResult:
        if condition_result is None:
            condition_result = self._default_reply_check_result(step)
        if condition_result is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="condition_result is required for condition steps",
            )

        branch = self._branch_for_condition(condition_result)
        next_step_id = self._branch_step_id(steps, branch)
        if next_step_id is None:
            updated = await self._run_repository.update(
                run.id,
                status="completed",
                next_execution_at=None,
            )
            assert updated is not None
            return StepExecutionResult(
                workflow_run_id=updated.id,
                step_id=step.id,
                step_type=step.type,
                action="evaluated_condition",
                status=updated.status,
            )

        updated = await self._run_repository.update(
            run.id,
            current_step=next_step_id,
            status="queued",
            next_execution_at=datetime.now(UTC),
        )
        assert updated is not None
        return StepExecutionResult(
            workflow_run_id=updated.id,
            step_id=step.id,
            step_type=step.type,
            action="evaluated_condition",
            status=updated.status,
            next_step_id=next_step_id,
            next_execution_at=updated.next_execution_at,
        )

    async def process_due_runs(self, *, limit: int = 500) -> int:
        """Enqueue resume tasks for workflow runs past their wait time (safety net if Celery eta missed)."""
        from app.workers.celery_app import WORKFLOW_QUEUE
        from app.workers.workflow_worker import resume_workflow_task

        now = datetime.now(UTC)
        due_runs = await self._run_repository.find_due(as_of=now, limit=limit)
        enqueued = 0
        for run in due_runs:
            record = await workflow_repository.get_by_id_only(run.workflow_id)
            if record is None:
                continue
            resume_workflow_task.apply_async(
                args=[record.user_id, run.id],
                queue=WORKFLOW_QUEUE,
            )
            enqueued += 1
        return enqueued


workflow_execution_service = WorkflowExecutionService()
