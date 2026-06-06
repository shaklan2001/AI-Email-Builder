"""Workflow activation — version snapshot, execution records, draft → active."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.repositories.workflow_repository import WorkflowRecord
from app.services.workflow_activation_service import WorkflowActivationService


def _approved_state() -> dict[str, object]:
    return {
        "review_status": "approved",
        "workflow": {
            "steps": [
                {
                    "id": "s1",
                    "type": "send_email",
                    "email": {
                        "subject": "Hi",
                        "html_content": "<p>x</p>",
                        "plain_text_content": "x",
                    },
                },
            ],
            "recipient_emails": ["a@example.com", "b@example.com"],
        },
    }


def _draft_record() -> WorkflowRecord:
    now = datetime.now(UTC)
    return WorkflowRecord(
        id="wf_test123456",
        user_id="user_1",
        name="Test",
        status="draft",
        workflow_definition={
            "steps": [{"id": "s1", "type": "send_email"}],
            "recipient_emails": ["a@example.com", "b@example.com"],
        },
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_activate_creates_version_execution_records_and_active_status() -> None:
    service = WorkflowActivationService()
    record = _draft_record()
    activated = WorkflowRecord(
        id=record.id,
        user_id=record.user_id,
        name=record.name,
        status="active",
        workflow_definition=record.workflow_definition,
        active_version=1,
        activated_at=datetime.now(UTC),
        created_at=record.created_at,
        updated_at=datetime.now(UTC),
    )
    version_doc = MagicMock()
    version_doc.version = 1
    mock_run = MagicMock()
    mock_run.id = "run_1"

    workflow_raw = _approved_state()["workflow"]
    assert isinstance(workflow_raw, dict)

    with (
        patch(
            "app.services.workflow_activation_service.workflow_repository.get_by_id",
            new_callable=AsyncMock,
            return_value=record,
        ),
        patch(
            "app.services.workflow_activation_service.conversation_repository.get_conversation_state",
            new_callable=AsyncMock,
            return_value=_approved_state(),
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
            return_value=activated,
        ),
        patch(
            "app.services.workflow_activation_service.execution_repository.find_by_workflow_and_lead",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.workflow_activation_service.execution_repository.create",
            new_callable=AsyncMock,
        ) as mock_exec_create,
        patch(
            "app.services.workflow_activation_service.workflow_execution_service.create_run",
            new_callable=AsyncMock,
            return_value=mock_run,
        ) as mock_create_run,
        patch(
            "app.services.workflow_activation_service.execute_workflow_step_task.apply_async",
        ),
    ):
        result = await service.activate(user_id="user_1", workflow_id="wf_test123456")

    assert result.status == "active"
    assert result.active_version == 1
    assert result.executions_created == 2
    assert result.runs_queued == 2
    assert result.activated_at
    assert mock_exec_create.await_count == 2
    assert mock_create_run.await_count == 2


@pytest.mark.asyncio
async def test_activate_rejects_without_review_approval() -> None:
    service = WorkflowActivationService()
    record = _draft_record()

    with (
        patch(
            "app.services.workflow_activation_service.workflow_repository.get_by_id",
            new_callable=AsyncMock,
            return_value=record,
        ),
        patch(
            "app.services.workflow_activation_service.conversation_repository.get_conversation_state",
            new_callable=AsyncMock,
            return_value={"review_status": "pending", "workflow": record.workflow_definition},
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await service.activate(user_id="user_1", workflow_id="wf_test123456")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_activate_rejects_already_active() -> None:
    service = WorkflowActivationService()
    record = _draft_record()
    record = record.model_copy(update={"status": "active"})

    with patch(
        "app.services.workflow_activation_service.workflow_repository.get_by_id",
        new_callable=AsyncMock,
        return_value=record,
    ):
        with pytest.raises(HTTPException) as exc:
            await service.activate(user_id="user_1", workflow_id="wf_test123456")
    assert exc.value.status_code == 400
