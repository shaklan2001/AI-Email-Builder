from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.workflows import delete_workflow
from app.core.security import CurrentUser


@pytest.mark.asyncio
async def test_delete_workflow_returns_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import workflow_delete_service as delete_mod

    delete_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(delete_mod.workflow_delete_service, "delete_workflow", delete_mock)

    response = await delete_workflow(
        workflow_id="wf_abc123def456",
        current_user=CurrentUser(user_id="user_1"),
    )
    assert response.success is True
    assert response.data.workflow_id == "wf_abc123def456"
    assert response.data.message == "Workflow deleted successfully."
    delete_mock.assert_awaited_once_with(
        user_id="user_1",
        workflow_id="wf_abc123def456",
    )


@pytest.mark.asyncio
async def test_delete_workflow_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import workflow_delete_service as delete_mod

    monkeypatch.setattr(
        delete_mod.workflow_delete_service,
        "delete_workflow",
        AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Workflow not found"),
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await delete_workflow(
            workflow_id="wf_abc123def456",
            current_user=CurrentUser(user_id="user_1"),
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_workflow_rejects_reserved_id() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await delete_workflow(
            workflow_id="new",
            current_user=CurrentUser(user_id="user_1"),
        )
    assert exc_info.value.status_code == 400
