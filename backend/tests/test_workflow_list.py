from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.api.workflows import list_workflows
from app.core.security import CurrentUser
from app.repositories.workflow_repository import WorkflowRecord


@pytest.mark.asyncio
async def test_list_workflows_returns_empty_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.repositories import workflow_repository as repo_mod

    monkeypatch.setattr(
        repo_mod.workflow_repository,
        "list_by_user_id",
        AsyncMock(return_value=[]),
    )

    response = await list_workflows(current_user=CurrentUser(user_id="user_1"))
    assert response.success is True
    assert response.data == []


@pytest.mark.asyncio
async def test_list_workflows_returns_user_workflows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.repositories import workflow_repository as repo_mod

    created_at = datetime(2024, 1, 1, tzinfo=UTC)
    records = [
        WorkflowRecord(
            id="wf_abc123",
            user_id="user_1",
            name="Campaign A",
            status="draft",
            created_at=created_at,
            updated_at=created_at,
        ),
    ]
    monkeypatch.setattr(
        repo_mod.workflow_repository,
        "list_by_user_id",
        AsyncMock(return_value=records),
    )

    response = await list_workflows(current_user=CurrentUser(user_id="user_1"))
    assert response.success is True
    assert len(response.data) == 1
    assert response.data[0].id == "wf_abc123"
    assert response.data[0].name == "Campaign A"
    assert response.data[0].status == "draft"
    assert response.data[0].created_at == created_at.isoformat()
