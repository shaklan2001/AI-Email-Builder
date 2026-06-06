"""Persist recipients to conversation state and workflow definition."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.services.recipient_service import RecipientService


@pytest.mark.asyncio
async def test_add_recipients_persists_to_state_and_workflow() -> None:
    service = RecipientService()
    record = AsyncMock()
    record.workflow_definition = {
        "steps": [{"id": "s1", "type": "send_email"}],
    }

    state = {
        "workflow_id": "wf_test123456",
        "user_id": "user_1",
        "recipients": [],
        "workflow": {"steps": [{"id": "s1", "type": "send_email"}]},
    }

    with (
        patch(
            "app.services.recipient_service.workflow_repository.get_by_id",
            new_callable=AsyncMock,
            return_value=record,
        ),
        patch(
            "app.services.recipient_service.conversation_repository.get_conversation_state",
            new_callable=AsyncMock,
            return_value=state,
        ),
        patch(
            "app.services.recipient_service.save_conversation_state",
            new_callable=AsyncMock,
            return_value=state,
        ) as mock_save,
        patch(
            "app.services.recipient_service.workflow_repository.upsert_workflow_definition",
            new_callable=AsyncMock,
        ) as mock_upsert,
    ):
        result = await service.add_recipients(
            user_id="user_1",
            workflow_id="wf_test123456",
            emails=["lead@example.com"],
        )

    assert result["valid_count"] == 1
    assert result["valid_emails"] == ["lead@example.com"]
    mock_save.assert_awaited_once()
    saved_state = mock_save.await_args.args[2]
    assert saved_state["recipients"] == [{"email": "lead@example.com"}]
    assert saved_state["workflow"]["recipient_emails"] == ["lead@example.com"]
    mock_upsert.assert_awaited()


@pytest.mark.asyncio
async def test_add_recipients_rejects_invalid_email() -> None:
    service = RecipientService()
    record = AsyncMock()
    record.workflow_definition = None

    with (
        patch(
            "app.services.recipient_service.workflow_repository.get_by_id",
            new_callable=AsyncMock,
            return_value=record,
        ),
        patch(
            "app.services.recipient_service.conversation_repository.get_conversation_state",
            new_callable=AsyncMock,
            return_value={"recipients": []},
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await service.add_recipients(
                user_id="user_1",
                workflow_id="wf_test123456",
                emails=["not-an-email"],
            )

    assert exc_info.value.status_code == 400
