from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.services.workflow_status_service import WorkflowStatusService


@pytest.mark.asyncio
async def test_pause_active_workflow(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.repositories import workflow_repository as repo_mod

    record = type(
        "R",
        (),
        {
            "id": "wf_test123456",
            "user_id": "user_1",
            "name": "Test",
            "status": "active",
            "workflow_definition": None,
            "active_version": 1,
            "activated_at": None,
            "created_at": None,
            "updated_at": None,
        },
    )()

    async def get_by_id(_user_id: str, _workflow_id: str):
        return record

    async def update_status(**_kwargs):
        record.status = "paused"
        return record

    monkeypatch.setattr(repo_mod.workflow_repository, "get_by_id", get_by_id)
    monkeypatch.setattr(repo_mod.workflow_repository, "update_status", update_status)

    monkeypatch.setattr(
        "app.services.workflow_status_service.workflow_run_queue_service.requeue_workflow_runs",
        AsyncMock(return_value=0),
    )

    updated, runs_enqueued = await WorkflowStatusService().update_status(
        user_id="user_1",
        workflow_id="wf_test123456",
        new_status="paused",
    )
    assert updated.status == "paused"
    assert runs_enqueued == 0


@pytest.mark.asyncio
async def test_rejects_invalid_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.repositories import workflow_repository as repo_mod

    record = type("R", (), {"id": "wf_test123456", "status": "draft"})()

    async def get_by_id(_user_id: str, _workflow_id: str):
        return record

    monkeypatch.setattr(repo_mod.workflow_repository, "get_by_id", get_by_id)

    with pytest.raises(HTTPException) as exc_info:
        await WorkflowStatusService().update_status(
            user_id="user_1",
            workflow_id="wf_test123456",
            new_status="paused",
        )
    assert exc_info.value.status_code == 400
