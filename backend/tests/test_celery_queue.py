"""Tests for Celery + Redis queue integration (spec 21)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.workflow_execution_service import StepExecutionResult
from app.workers.celery_app import EMAIL_QUEUE, RETRY_QUEUE, WORKFLOW_QUEUE, celery_app
from app.workers.dispatch import dispatch_after_step, enqueue_send_email


@pytest.fixture(autouse=True)
def celery_eager() -> None:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
    yield
    celery_app.conf.update(
        task_always_eager=False,
        task_eager_propagates=False,
    )


def test_celery_queues_configured() -> None:
    queue_names = {queue.name for queue in celery_app.conf.task_queues}
    assert queue_names == {WORKFLOW_QUEUE, EMAIL_QUEUE, RETRY_QUEUE}


def test_task_routes_use_expected_queues() -> None:
    routes = celery_app.conf.task_routes
    assert routes["app.workers.workflow_worker.execute_workflow_step_task"]["queue"] == WORKFLOW_QUEUE
    assert routes["app.workers.workflow_worker.resume_workflow_task"]["queue"] == WORKFLOW_QUEUE
    assert routes["app.workers.email_worker.send_email_task"]["queue"] == EMAIL_QUEUE


def test_dispatch_after_step_schedules_resume_with_eta() -> None:
    resume_at = datetime.now(UTC) + timedelta(days=3)
    result = StepExecutionResult(
        workflow_run_id="run_1",
        step_id="step_wait",
        step_type="wait",
        action="scheduled_wait",
        status="waiting",
        next_execution_at=resume_at,
    )

    with patch("app.workers.workflow_worker.resume_workflow_task.apply_async") as mock_resume:
        dispatch_after_step(user_id="user_1", result=result)

    mock_resume.assert_called_once()
    call_kwargs = mock_resume.call_args.kwargs
    assert call_kwargs["args"] == ["user_1", "run_1"]
    assert call_kwargs["queue"] == WORKFLOW_QUEUE
    assert call_kwargs["eta"] is not None


def test_dispatch_after_step_chains_execute_when_queued() -> None:
    result = StepExecutionResult(
        workflow_run_id="run_2",
        step_id="step_1",
        step_type="send_email",
        action="sent_email",
        status="queued",
        next_step_id="step_2",
        next_execution_at=datetime.now(UTC),
    )

    with patch(
        "app.workers.workflow_worker.execute_workflow_step_task.apply_async",
    ) as mock_execute:
        dispatch_after_step(user_id="user_1", result=result)

    mock_execute.assert_called_once_with(
        args=["user_1", "run_2"],
        queue=WORKFLOW_QUEUE,
    )


def test_enqueue_send_email_uses_email_queue() -> None:
    with patch("app.workers.email_worker.send_email_task.apply_async") as mock_send:
        enqueue_send_email(user_id="user_1", workflow_run_id="run_3")

    mock_send.assert_called_once_with(
        args=["user_1", "run_3"],
        queue=EMAIL_QUEUE,
    )


@pytest.mark.asyncio
async def test_run_execute_workflow_step_routes_send_email_to_queue() -> None:
    from app.workers.workflow_runner import run_execute_workflow_step

    with (
        patch(
            "app.workers.workflow_runner._current_step_type",
            new_callable=AsyncMock,
            return_value="send_email",
        ),
        patch("app.workers.workflow_runner.enqueue_send_email") as mock_enqueue,
    ):
        outcome = await run_execute_workflow_step(
            user_id="user_1",
            workflow_run_id="run_4",
        )

    assert outcome is None
    mock_enqueue.assert_called_once_with(user_id="user_1", workflow_run_id="run_4")


@pytest.mark.asyncio
async def test_activation_enqueues_execute_task_per_recipient() -> None:
    from app.services.workflow_activation_service import WorkflowActivationService

    service = WorkflowActivationService()
    workflow_raw = {
        "steps": [{"id": "s1", "type": "send_email"}],
        "recipient_emails": ["a@example.com", "b@example.com"],
    }

    mock_record = MagicMock()
    mock_record.status = "draft"

    mock_run = MagicMock()
    mock_run.id = "run_x"

    version_doc = MagicMock()
    version_doc.version = 1

    with (
        patch(
            "app.services.workflow_activation_service.workflow_repository.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_record,
        ),
        patch(
            "app.services.workflow_activation_service.conversation_repository.get_conversation_state",
            new_callable=AsyncMock,
            return_value={
                "review_status": "approved",
                "workflow": workflow_raw,
            },
        ),
        patch.object(
            service,
            "_resolve_workflow_for_activation",
            new_callable=AsyncMock,
            return_value=workflow_raw,
        ),
        patch(
            "app.services.workflow_activation_service.workflow_version_service.create_snapshot",
            new_callable=AsyncMock,
            return_value=version_doc,
        ),
        patch(
            "app.services.workflow_activation_service.workflow_repository.activate",
            new_callable=AsyncMock,
            return_value=mock_record,
        ),
        patch(
            "app.services.workflow_activation_service.execution_repository.find_by_workflow_and_lead",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.workflow_activation_service.execution_repository.create",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.workflow_activation_service.workflow_execution_service.create_run",
            new_callable=AsyncMock,
            return_value=mock_run,
        ),
        patch(
            "app.services.workflow_activation_service.execute_workflow_step_task.apply_async",
        ) as mock_enqueue,
    ):
        result = await service.activate(user_id="user_1", workflow_id="wf_test")

    assert result.status == "active"
    assert result.runs_queued == 2
    assert mock_enqueue.call_count == 2
