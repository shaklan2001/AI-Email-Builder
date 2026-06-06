"""Wait step scheduling — hours, days, weeks (spec 20)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.email import EmailBodyVersion, GeneratedEmailContent
from app.schemas.follow_up_delay import FollowUpDelay
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.workflow_execution_service import WorkflowExecutionService


def _email_step(step_id: str) -> WorkflowStep:
    body = EmailBodyVersion(
        subject="Hi",
        html_content="<p>Hi</p>",
        plain_text_content="Hi",
    )
    content = GeneratedEmailContent(
        ai_generated_version=body,
        final_user_version=body,
    )
    return WorkflowStep(id=step_id, type="send_email", name="Email", email=content)


def _definition_with_wait(*, value: int, unit: str) -> WorkflowDefinition:
    return WorkflowDefinition(
        follow_up_delay=FollowUpDelay(value=value, unit=unit),  # type: ignore[arg-type]
        steps=[
            _email_step("step_1"),
            WorkflowStep(id="step_2", type="wait", value=value, unit=unit),  # type: ignore[arg-type]
            WorkflowStep(id="step_3", type="condition", condition="reply_received"),
            _email_step("step_4"),
        ],
    )


@pytest.mark.parametrize(
    ("value", "unit", "expected_delta"),
    [
        (4, "hours", timedelta(hours=4)),
        (3, "days", timedelta(days=3)),
        (2, "weeks", timedelta(weeks=2)),
    ],
)
@pytest.mark.asyncio
async def test_send_email_schedules_wait_with_correct_duration(
    value: int,
    unit: str,
    expected_delta: timedelta,
) -> None:
    definition = _definition_with_wait(value=value, unit=unit)
    run_repo = MagicMock()
    stored_run = MagicMock()
    stored_run.id = "run_1"
    stored_run.workflow_id = "wf_1"
    stored_run.recipient_id = "lead@example.com"
    stored_run.current_step = "step_1"
    stored_run.status = "queued"

    async def fake_create(**kwargs: object) -> MagicMock:
        return stored_run

    async def fake_get(run_id: str) -> MagicMock:
        return stored_run

    async def fake_update(run_id: str, **kwargs: object) -> MagicMock:
        for key, val in kwargs.items():
            setattr(stored_run, key, val)
        return stored_run

    run_repo.create = AsyncMock(side_effect=fake_create)
    run_repo.get_by_id = AsyncMock(side_effect=fake_get)
    run_repo.update = AsyncMock(side_effect=fake_update)
    run_repo.find_by_workflow_and_recipient = AsyncMock(return_value=None)

    email_svc = MagicMock()
    email_svc.send_email = AsyncMock(
        return_value=MagicMock(resend_message_id="msg_1"),
    )

    service = WorkflowExecutionService(run_repository=run_repo, email=email_svc)
    service._load_workflow_definition_raw = AsyncMock(  # type: ignore[method-assign]
        return_value={
            **definition.model_dump(mode="json"),
            "recipient_emails": ["lead@example.com"],
        },
    )

    before = datetime.now(UTC)
    result = await service.execute_step("run_1", user_id="user_1")
    after = datetime.now(UTC)

    assert result.action == "sent_email"
    assert stored_run.status == "waiting"
    assert stored_run.current_step == "step_2"
    assert stored_run.next_execution_at is not None

    resume_at = stored_run.next_execution_at
    lower = before + expected_delta - timedelta(seconds=2)
    upper = after + expected_delta + timedelta(seconds=2)
    assert lower <= resume_at <= upper


@pytest.mark.asyncio
async def test_wait_step_sets_resume_at_from_step_units() -> None:
    definition = _definition_with_wait(value=7, unit="days")
    run = MagicMock()
    run.id = "run_w"
    run.workflow_id = "wf_1"
    run.recipient_id = "lead@example.com"
    run.current_step = "step_2"
    run.status = "running"

    run_repo = MagicMock()
    run_repo.get_by_id = AsyncMock(return_value=run)
    run_repo.update = AsyncMock(return_value=run)

    service = WorkflowExecutionService(run_repository=run_repo)
    service._load_workflow_definition_raw = AsyncMock(  # type: ignore[method-assign]
        return_value=definition.model_dump(mode="json"),
    )

    now = datetime.now(UTC)
    result = await service.execute_step("run_w", user_id="user_1", now=now)

    assert result.action == "scheduled_wait"
    assert result.next_execution_at == now + timedelta(days=7)
