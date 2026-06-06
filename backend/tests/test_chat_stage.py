from app.langgraph.state import ConversationState
from app.schemas.conversation_stage import ConversationStage
from app.services.conversation_stage import resolve_stage
from app.services.conversation_state_service import (
    normalize_conversation_state,
    sanitize_loaded_state,
)


def test_resolve_stage_discovery() -> None:
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [],
    }
    assert resolve_stage(state) == ConversationStage.DISCOVERY


def test_resolve_stage_campaign_brief() -> None:
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [],
        "product_info": "AI CRM",
        "brief_status": "pending_approval",
        "campaign_brief": {"productInfo": "AI CRM"},
    }
    assert resolve_stage(state) == ConversationStage.CAMPAIGN_BRIEF


def test_sanitize_loaded_state_strips_stale_workflow_during_discovery() -> None:
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [],
        "current_stage": ConversationStage.DISCOVERY,
        "workflow": {"steps": [{"id": "step_1", "type": "send_email"}]},
        "campaign_brief": None,
    }
    healed = sanitize_loaded_state(state)
    assert healed.get("workflow") is None
    assert healed.get("email_templates") == []
    assert healed.get("current_stage") == ConversationStage.DISCOVERY


def test_normalize_populates_email_templates_from_workflow() -> None:
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [],
        "brief_approved": True,
        "brief_status": "approved",
        "workflow": {
            "steps": [
                {
                    "id": "step_1",
                    "type": "send_email",
                    "email": {
                        "subject": "Hello",
                        "html_content": "<p>Hi</p>",
                        "plain_text_content": "Hi",
                    },
                },
            ],
        },
    }
    normalized = normalize_conversation_state(state)
    assert len(normalized.get("email_templates") or []) == 1
    assert normalized["email_templates"][0]["step_id"] == "step_1"
