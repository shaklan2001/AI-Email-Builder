"""In-memory stores and helpers for end-to-end integration tests (spec 45)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from app.models.workflow_run import WorkflowRun
from app.providers.email.base import EmailProvider
from app.repositories.workflow_repository import WorkflowRecord
from app.schemas.email import EmailBodyVersion, GeneratedEmailContent
from app.schemas.email_message import SendEmailResult
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.workflow_execution_service import WorkflowExecutionService


USER_ID = "e2e_user"
WORKFLOW_ID = "wf_e2e00000001"
LEAD_EMAIL = "lead@example.com"


def _email_step(
    step_id: str,
    *,
    name: str = "Email",
    branch: str | None = None,
) -> WorkflowStep:
    return WorkflowStep(
        id=step_id,
        type="send_email",
        name=name,
        branch=branch,  # type: ignore[arg-type]
        email=GeneratedEmailContent(
            ai_generated_version=EmailBodyVersion(
                subject=f"Subject {step_id}",
                html_content=f"<p>{step_id}</p>",
                plain_text_content=f"Plain {step_id}",
            ),
            final_user_version=EmailBodyVersion(
                subject=f"Subject {step_id}",
                html_content=f"<p>{step_id}</p>",
                plain_text_content=f"Plain {step_id}",
            ),
        ),
    )


def conditional_workflow_definition() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_type="conditional",
        follow_up_delay={"value": 1, "unit": "hours"},
        steps=[
            _email_step("step_1", name="Initial Email"),
            WorkflowStep(id="step_2", type="wait", days=1),
            WorkflowStep(id="step_3", type="condition", condition="reply_received"),
            _email_step("step_4", name="Follow Up", branch="no"),
            _email_step("step_5", name="Demo Call", branch="yes"),
            WorkflowStep(id="step_6", type="end"),
        ],
    )


def campaign_conversation_state() -> dict[str, Any]:
    workflow = conditional_workflow_definition().model_dump()
    workflow["recipient_emails"] = [LEAD_EMAIL]
    return {
        "user_id": USER_ID,
        "workflow_id": WORKFLOW_ID,
        "product_info": "ZyLabs AI email automation",
        "campaign_name": "ZyLabs Launch",
        "audience": "B2B SaaS founders",
        "cta": "Book a demo",
        "landing_page": "https://zylabs.example.com",
        "brief_approved": True,
        "review_status": "pending",
        "workflow": workflow,
        "recipients": [LEAD_EMAIL],
    }


def approved_conversation_state() -> dict[str, Any]:
    state = campaign_conversation_state()
    state["review_status"] = "approved"
    return state


class MockEmailProvider(EmailProvider):
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []
        self.fail_until_attempt = 0
        self.attempts = 0

    async def send_email(
        self,
        *,
        subject: str,
        html_content: str,
        plain_text_content: str,
        recipients: list[str],
        reply_to: str | None = None,
        tags: dict[str, str] | None = None,
        workflow_id: str | None = None,
        lead_id: str | None = None,
    ) -> str:
        self.attempts += 1
        if self.attempts <= self.fail_until_attempt:
            from app.providers.email.base import EmailProviderError

            raise EmailProviderError("Simulated send failure")
        self.sent.append(
            {
                "subject": subject,
                "html_content": html_content,
                "plain_text_content": plain_text_content,
                "recipients": list(recipients),
                "workflow_id": workflow_id,
                "lead_id": lead_id,
            },
        )
        return f"msg_e2e_{self.attempts}"


class InMemoryRunRepository:
    def __init__(self) -> None:
        self._runs: dict[str, WorkflowRun] = {}
        self._counter = 0

    async def create(
        self,
        *,
        workflow_id: str,
        recipient_id: str,
        current_step: str,
        status: str = "queued",
        next_execution_at: datetime | None = None,
    ) -> WorkflowRun:
        self._counter += 1
        now = datetime.now(UTC)
        run = WorkflowRun(
            id=f"run_e2e_{self._counter}",
            workflow_id=workflow_id,
            recipient_id=recipient_id,
            current_step=current_step,
            status=status,  # type: ignore[arg-type]
            next_execution_at=next_execution_at,
            created_at=now,
            updated_at=now,
        )
        self._runs[run.id] = run
        return run

    async def get_by_id(self, run_id: str) -> WorkflowRun | None:
        return self._runs.get(run_id)

    async def update(
        self,
        run_id: str,
        *,
        current_step: str | None = None,
        status: str | None = None,
        next_execution_at: datetime | None = ...,  # type: ignore[assignment]
    ) -> WorkflowRun | None:
        run = self._runs.get(run_id)
        if run is None:
            return None
        data = run.model_dump()
        if current_step is not None:
            data["current_step"] = current_step
        if status is not None:
            data["status"] = status
        if next_execution_at is not ...:
            data["next_execution_at"] = next_execution_at
        data["updated_at"] = datetime.now(UTC)
        updated = WorkflowRun.model_validate(data)
        self._runs[run_id] = updated
        return updated

    async def find_by_workflow_and_recipient(
        self,
        workflow_id: str,
        recipient_id: str,
    ) -> WorkflowRun | None:
        for run in self._runs.values():
            if run.workflow_id == workflow_id and run.recipient_id == recipient_id:
                return run
        return None

    async def find_active_by_recipient(
        self,
        recipient: str,
        *,
        workflow_id: str | None = None,
    ) -> list[WorkflowRun]:
        active = {"queued", "running", "waiting"}
        runs = [
            run
            for run in self._runs.values()
            if run.recipient_id == recipient and run.status in active
        ]
        if workflow_id:
            runs = [r for r in runs if r.workflow_id == workflow_id]
        return runs


class InMemoryConversationStore:
    def __init__(self, state: dict[str, Any]) -> None:
        self._state = dict(state)

    async def get_conversation_state(self, user_id: str, workflow_id: str) -> dict[str, Any] | None:
        if user_id == USER_ID and workflow_id == WORKFLOW_ID:
            return dict(self._state)
        return None

    async def get_campaign_state(self, user_id: str, workflow_id: str) -> dict[str, Any] | None:
        return await self.get_conversation_state(user_id, workflow_id)


def draft_workflow_record() -> WorkflowRecord:
    now = datetime.now(UTC)
    return WorkflowRecord(
        id=WORKFLOW_ID,
        user_id=USER_ID,
        name="E2E Campaign",
        status="draft",
        workflow_definition=conditional_workflow_definition().model_dump(),
        created_at=now,
        updated_at=now,
    )


def build_execution_service(
    run_repo: InMemoryRunRepository,
    email_provider: MockEmailProvider,
) -> WorkflowExecutionService:
    email_svc = MagicMock()
    message_repo = AsyncMock()
    message_repo.create_sent = AsyncMock()
    message_repo.create_failed = AsyncMock()
    analytics = AsyncMock()
    analytics.record_sent = AsyncMock()
    analytics.record_failed = AsyncMock()
    email_svc._message_repository = message_repo
    email_svc._analytics_service = analytics
    email_svc._email_provider = email_provider

    async def _send_email(**kwargs: object) -> SendEmailResult:
        lead_id = str(kwargs["lead_id"])
        message_id = await email_provider.send_email(
            subject=str(kwargs["subject"]),
            html_content=str(kwargs["html_content"]),
            plain_text_content=str(kwargs["plain_text_content"]),
            recipients=[lead_id],
            workflow_id=str(kwargs.get("workflow_id") or ""),
            lead_id=lead_id,
        )
        return SendEmailResult(
            resend_message_id=message_id,
            workflow_id=str(kwargs["workflow_id"]),
            lead_id=lead_id,
            step_id=str(kwargs["step_id"]) if kwargs.get("step_id") else None,
        )

    email_svc.send_email = AsyncMock(side_effect=_send_email)
    email_svc._provider = MagicMock(return_value=email_provider)

    svc = WorkflowExecutionService(run_repository=run_repo, email=email_svc, analytics=analytics)
    workflow_raw = conditional_workflow_definition().model_dump()
    workflow_raw["recipient_emails"] = [LEAD_EMAIL]
    svc._load_workflow_definition_raw = AsyncMock(return_value=workflow_raw)  # type: ignore[method-assign]
    return svc
