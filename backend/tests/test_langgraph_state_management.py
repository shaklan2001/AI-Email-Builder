"""LangGraph conversation state management (feature spec 33)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.langgraph.state import ConversationState
from app.schemas.conversation_stage import ConversationStage
from app.services.conversation_state_service import (
    empty_conversation_state,
    normalize_conversation_state,
    sanitize_loaded_state,
)
from app.services.conversation_stage import resolve_stage
from app.services.persistence import save_conversation_state
from app.services.workflow_state_response import (
    brief_from_state,
    workflow_from_state,
)


def test_empty_conversation_state_has_spec_fields() -> None:
    state = empty_conversation_state(user_id="user_1", workflow_id="wf_abc123456789")

    assert state["messages"] == []
    assert state["campaign_brief"] is None
    assert state["workflow"] is None
    assert state["email_templates"] == []
    assert state["recipients"] == []
    assert isinstance(state["missing_fields"], list)
    assert "product_info" in state["missing_fields"]
    assert state["current_stage"] == ConversationStage.DISCOVERY
    assert state["campaign_id"] == "wf_abc123456789"
    assert state["approval_status"] == "collecting"
    assert state["conversation_threads"] == []
    assert state["generated_responses"] == []


def test_stages_match_spec() -> None:
    expected = {
        "discovery",
        "campaign_brief",
        "workflow_generation",
        "email_generation",
        "review",
        "activation",
    }
    assert {member.value for member in ConversationStage} == expected


def test_sanitize_strips_stale_workflow_before_brief_approval() -> None:
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [{"role": "user", "content": "Sell CRM"}],
        "product_info": "CRM",
        "brief_approved": False,
        "workflow": {
            "steps": [{"id": "s1", "type": "send_email", "email": {"subject": "Old"}}],
        },
        "campaign_brief": {"productInfo": "Other product"},
    }
    healed = sanitize_loaded_state(state)
    assert healed.get("workflow") is None
    assert healed.get("email_templates") == []
    assert workflow_from_state(healed) is None


def test_workflow_preview_hidden_during_discovery() -> None:
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [],
        "product_info": "CRM",
        "workflow": {"steps": [{"id": "s1", "type": "send_email"}]},
    }
    assert workflow_from_state(sanitize_loaded_state(state)) is None


def test_brief_preview_only_when_stage_allows() -> None:
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [],
        "product_info": "CRM",
        "follow_up_delay": {"value": 3, "unit": "days"},
        "campaign_brief": {
            "campaignName": "Test",
            "productInfo": "CRM",
            "audience": "SMBs",
            "cta": "Learn More",
            "tone": "Professional",
            "followUpDelay": "3 Days",
            "replyHandling": "AI Auto Reply",
            "toolsAvailable": ["Company Information", "Demo Booking"],
        },
        "brief_status": "pending_approval",
    }
    assert brief_from_state(normalize_conversation_state(state)) is not None


@pytest.mark.asyncio
async def test_save_conversation_state_persists_normalized_stage() -> None:
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "thread_id": "wf_abc123456789",
        "messages": [{"role": "user", "content": "hello"}],
        "product_info": "CRM",
        "follow_up_delay": {"value": 2, "unit": "days"},
    }
    with patch(
        "app.services.persistence.conversation_repository.upsert_conversation_state",
        new_callable=AsyncMock,
    ) as upsert_conv, patch(
        "app.services.persistence.workflow_repository.clear_workflow_definition",
        new_callable=AsyncMock,
    ) as clear_wf:
        saved = await save_conversation_state("user_1", "wf_abc123456789", state)

    upsert_conv.assert_awaited_once()
    clear_wf.assert_awaited_once()
    assert saved["current_stage"] == resolve_stage(saved)
    assert "missing_fields" in saved


@pytest.mark.asyncio
async def test_new_workflow_initialize_empty_session() -> None:
    from app.services.workflow_session_service import workflow_session_service

    with patch(
        "app.services.workflow_session_service.save_conversation_state",
        new_callable=AsyncMock,
    ) as save_state:
        await workflow_session_service.initialize_empty_session(
            user_id="user_1",
            workflow_id="wf_abc123456789",
        )

    save_state.assert_awaited_once()
    saved = save_state.await_args.args[2]
    assert saved["messages"] == []
    assert saved.get("workflow") is None
    assert saved["current_stage"] == ConversationStage.DISCOVERY
