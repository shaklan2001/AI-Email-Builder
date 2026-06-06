"""Workflow review stage — approval storage and activation gate."""

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch

from app.langgraph.state import ConversationState
from app.schemas.conversation_stage import ConversationStage
from app.services.conversation_stage import resolve_stage
from app.services.review_actions import parse_review_user_action
from app.services.review_service import apply_review_approve, build_review_data


def test_parse_review_actions() -> None:
    assert parse_review_user_action("Looks Good") == "approve"
    assert parse_review_user_action("Edit Campaign Details") == "edit_campaign"
    assert parse_review_user_action("Regenerate Workflow") == "regenerate_workflow"


def test_resolve_stage_review_before_approval() -> None:
    state: ConversationState = {
        "brief_approved": True,
        "workflow": {
            "steps": [
                {"id": "s1", "type": "send_email", "email": {"subject": "Hi", "html_content": "<p>x</p>", "plain_text_content": "x"}},
            ],
        },
        "review_status": "pending",
    }
    assert resolve_stage(state) == ConversationStage.REVIEW


def test_resolve_stage_activation_after_approval() -> None:
    state: ConversationState = {
        "brief_approved": True,
        "workflow": {
            "steps": [
                {"id": "s1", "type": "send_email", "email": {"subject": "Hi", "html_content": "<p>x</p>", "plain_text_content": "x"}},
            ],
        },
        "review_status": "approved",
    }
    assert resolve_stage(state) == ConversationStage.ACTIVATION


def test_build_review_data_activation_locked() -> None:
    state: ConversationState = {
        "product_info": "CRM",
        "workflow": {"steps": [{"id": "s1", "type": "send_email", "name": "Intro"}]},
        "review_status": "pending",
    }
    data = build_review_data(state)
    assert data.review_status == "pending"
    assert data.activation_allowed is False


@pytest.mark.asyncio
async def test_activation_blocked_without_review_approval() -> None:
    from datetime import UTC, datetime

    from app.repositories.workflow_repository import WorkflowRecord
    from app.services.workflow_activation_service import WorkflowActivationService

    svc = WorkflowActivationService()
    record = WorkflowRecord(
        id="wf_abc123456789",
        user_id="user_1",
        name="Test",
        status="draft",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    with patch(
        "app.services.workflow_activation_service.workflow_repository.get_by_id",
        new_callable=AsyncMock,
        return_value=record,
    ), patch(
        "app.services.workflow_activation_service.conversation_repository.get_conversation_state",
        new_callable=AsyncMock,
        return_value={
            "review_status": "pending",
            "workflow": {"steps": [{"id": "s1", "type": "send_email"}]},
        },
    ):
        with pytest.raises(HTTPException) as exc:
            await svc.activate(user_id="user_1", workflow_id="wf_abc123456789")
    assert exc.value.status_code == 403


def test_apply_review_approve_sets_status() -> None:
    state: ConversationState = {
        "workflow": {"steps": [{"id": "s1", "type": "send_email"}]},
    }
    updates = apply_review_approve(state)
    assert updates.get("review_status") == "approved"
