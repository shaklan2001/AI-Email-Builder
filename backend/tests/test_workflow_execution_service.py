"""Tests for workflow execution engine (spec 20)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.workflow_run import WorkflowRun
from app.providers.email.base import EmailProvider
from app.schemas.email import EmailBodyVersion, GeneratedEmailContent
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.schemas.email_message import SendEmailResult
from app.services.workflow_execution_service import WorkflowExecutionService


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


def _sample_definition() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_type="conditional",
        steps=[
            _email_step("step_1", name="Initial Email"),
            WorkflowStep(id="step_2", type="wait", days=3),
            WorkflowStep(id="step_3", type="condition", condition="reply_received"),
            _email_step("step_4", name="Follow Up", branch="no"),
            _email_step("step_5", name="Demo Call", branch="yes"),
            WorkflowStep(id="step_6", type="end"),
        ],
    )


class MockEmailProvider(EmailProvider):
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    async def send_email(
        self,
        *,
        subject: str,
        html_content: str,
        plain_text_content: str,
        recipients: list[str],
        workflow_id: str | None = None,
        lead_id: str | None = None,
    ) -> str:
        self.sent.append(
            {
                "subject": subject,
                "html_content": html_content,
                "plain_text_content": plain_text_content,
                "recipients": recipients,
            },
        )
        return "msg_test_123"


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
            id=f"run_{self._counter}",
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


@pytest.fixture
def run_repo() -> InMemoryRunRepository:
    return InMemoryRunRepository()


@pytest.fixture
def email_provider() -> MockEmailProvider:
    return MockEmailProvider()


@pytest.fixture
def service(
    run_repo: InMemoryRunRepository,
    email_provider: MockEmailProvider,
) -> WorkflowExecutionService:
    email_svc = MagicMock()

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

    svc = WorkflowExecutionService(
        run_repository=run_repo,  # type: ignore[arg-type]
        email=email_svc,
    )
    sample = _sample_definition()
    svc._load_workflow_definition_raw = AsyncMock(  # type: ignore[method-assign]
        return_value=sample.model_dump(),
    )
    return svc


@pytest.mark.asyncio
async def test_create_run_starts_at_first_step(service: WorkflowExecutionService) -> None:
    run = await service.create_run(
        user_id="user_1",
        workflow_id="wf_1",
        recipient_id="lead@example.com",
    )
    assert run.current_step == "step_1"
    assert run.status == "queued"
    assert run.workflow_id == "wf_1"
    assert run.recipient_id == "lead@example.com"


@pytest.mark.asyncio
async def test_send_email_transitions_to_wait(
    service: WorkflowExecutionService,
    email_provider: MockEmailProvider,
    run_repo: InMemoryRunRepository,
) -> None:
    run = await service.create_run(
        user_id="user_1",
        workflow_id="wf_1",
        recipient_id="lead@example.com",
    )

    result = await service.execute_step(run.id, user_id="user_1")

    assert result.action == "sent_email"
    assert result.message_id == "msg_test_123"
    assert len(email_provider.sent) == 1
    assert email_provider.sent[0]["recipients"] == ["lead@example.com"]

    updated = await run_repo.get_by_id(run.id)
    assert updated is not None
    assert updated.current_step == "step_2"
    assert updated.status == "waiting"
    assert updated.next_execution_at is not None


@pytest.mark.asyncio
async def test_wait_resume_advances_to_condition(
    service: WorkflowExecutionService,
    run_repo: InMemoryRunRepository,
) -> None:
    run = await service.create_run(
        user_id="user_1",
        workflow_id="wf_1",
        recipient_id="lead@example.com",
    )
    await service.execute_step(run.id, user_id="user_1")

    after_send = await run_repo.get_by_id(run.id)
    assert after_send is not None
    resume_at = after_send.next_execution_at
    assert resume_at is not None

    result = await service.execute_step(
        run.id,
        user_id="user_1",
        now=resume_at + timedelta(seconds=1),
    )

    updated = await run_repo.get_by_id(run.id)
    assert updated is not None
    assert updated.current_step == "step_3"
    assert updated.status == "queued"
    assert result.action == "scheduled_wait"


@pytest.mark.asyncio
async def test_condition_routes_to_yes_branch(
    service: WorkflowExecutionService,
    run_repo: InMemoryRunRepository,
) -> None:
    run = await run_repo.create(
        workflow_id="wf_1",
        recipient_id="lead@example.com",
        current_step="step_3",
        status="running",
    )

    result = await service.execute_step(
        run.id,
        user_id="user_1",
        condition_result=True,
    )

    assert result.action == "evaluated_condition"
    assert result.next_step_id == "step_5"

    updated = await run_repo.get_by_id(run.id)
    assert updated is not None
    assert updated.current_step == "step_5"
    assert updated.status == "queued"


@pytest.mark.asyncio
async def test_condition_routes_to_no_branch(
    service: WorkflowExecutionService,
    run_repo: InMemoryRunRepository,
) -> None:
    run = await run_repo.create(
        workflow_id="wf_1",
        recipient_id="lead@example.com",
        current_step="step_3",
        status="running",
    )

    result = await service.execute_step(
        run.id,
        user_id="user_1",
        condition_result=False,
    )

    assert result.next_step_id == "step_4"

    updated = await run_repo.get_by_id(run.id)
    assert updated is not None
    assert updated.current_step == "step_4"


@pytest.mark.asyncio
async def test_condition_requires_result(
    service: WorkflowExecutionService,
    run_repo: InMemoryRunRepository,
) -> None:
    run = await run_repo.create(
        workflow_id="wf_1",
        recipient_id="lead@example.com",
        current_step="step_3",
        status="running",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.execute_step(run.id, user_id="user_1")
    assert exc_info.value.status_code == 400
    assert "condition_result" in exc_info.value.detail


@pytest.mark.asyncio
async def test_full_no_reply_path_sends_follow_up(
    service: WorkflowExecutionService,
    email_provider: MockEmailProvider,
    run_repo: InMemoryRunRepository,
) -> None:
    run = await service.create_run(
        user_id="user_1",
        workflow_id="wf_1",
        recipient_id="lead@example.com",
    )

    await service.execute_step(run.id, user_id="user_1")
    after_send = await run_repo.get_by_id(run.id)
    assert after_send is not None

    await service.execute_step(
        run.id,
        user_id="user_1",
        now=(after_send.next_execution_at or datetime.now(UTC)) + timedelta(seconds=1),
    )
    await service.execute_step(run.id, user_id="user_1", condition_result=False)
    await service.execute_step(run.id, user_id="user_1")
    await service.execute_step(run.id, user_id="user_1")

    assert len(email_provider.sent) == 2
    assert email_provider.sent[1]["subject"] == "Subject step_4"

    updated = await run_repo.get_by_id(run.id)
    assert updated is not None
    assert updated.status == "completed"


@pytest.mark.asyncio
async def test_branch_step_navigation_skips_other_branch(
    service: WorkflowExecutionService,
) -> None:
    branch = service._branch_step_id(_sample_definition().steps, "no")
    assert branch == "step_4"

    next_after_branch = service._next_linear_step_id(_sample_definition().steps, "step_4")
    assert next_after_branch == "step_6"


def test_resolve_recipient_email_from_id() -> None:
    raw = {"recipient_emails": ["lead@example.com"], "steps": []}
    email = WorkflowExecutionService._resolve_recipient_email(raw, "lead@example.com")
    assert email == "lead@example.com"


def test_resolve_recipient_email_fallback_to_id_when_email_shaped() -> None:
    email = WorkflowExecutionService._resolve_recipient_email({}, "lead@example.com")
    assert email == "lead@example.com"
