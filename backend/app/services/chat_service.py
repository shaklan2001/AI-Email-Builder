from dataclasses import dataclass

from app.langgraph.graph import get_campaign_graph
from app.langgraph.state import CampaignState, MessageDict
from app.providers.llm.base import LLMProviderError
from app.schemas.requests import (
    CampaignBriefFieldData,
    WorkflowDefinitionData,
)
from app.repositories.conversation_repository import conversation_repository
from app.services.brief_actions import parse_brief_user_action
from app.services.conversation_response import build_brief_edit_reply
from app.core.workflow_ids import assert_valid_workflow_id
from app.services.persistence import save_campaign_state
from app.services.workflow_state_response import brief_from_state, workflow_from_state

_LLM_UNAVAILABLE_REPLY = (
    "I'm having trouble reaching the AI service right now. Please try again in a moment."
)


@dataclass
class ChatProcessResult:
    message: str
    workflow: WorkflowDefinitionData | None
    campaign_brief: CampaignBriefFieldData | None = None
    brief_status: str | None = None


class ChatService:
    async def process_message(
        self,
        *,
        user_id: str,
        workflow_id: str,
        message: str,
    ) -> ChatProcessResult:
        assert_valid_workflow_id(workflow_id)
        state = await conversation_repository.get_campaign_state(user_id, workflow_id)
        if state is None:
            state = CampaignState(
                workflow_id=workflow_id,
                user_id=user_id,
                messages=[],
                campaign_name=None,
                business_goal=None,
                product_info=None,
                audience=None,
                tone=None,
                cta=None,
                landing_page=None,
                product_image=None,
                skipped_fields=[],
            )

        messages: list[MessageDict] = list(state.get("messages") or [])
        messages.append({"role": "user", "content": message})
        state["messages"] = messages

        brief_action = None
        if state.get("brief_status") == "pending_approval":
            brief_action = parse_brief_user_action(message)
            if brief_action == "approve":
                state["brief_approved"] = True
                state["brief_status"] = "approved"
            elif brief_action == "edit":
                state["brief_approved"] = False
                state["brief_status"] = "editing"
                state["campaign_brief"] = None
        elif state.get("brief_status") == "editing" and parse_brief_user_action(message) is None:
            state["brief_status"] = None
            state["campaign_brief"] = None

        try:
            result = await get_campaign_graph().ainvoke(state)
        except LLMProviderError:
            return ChatProcessResult(message=_LLM_UNAVAILABLE_REPLY, workflow=None)

        await save_campaign_state(user_id, workflow_id, result)
        reply = result.get("assistant_reply", "").strip()
        if brief_action == "edit":
            reply = build_brief_edit_reply()
            result["assistant_reply"] = reply
        if not reply:
            return ChatProcessResult(message=_LLM_UNAVAILABLE_REPLY, workflow=None)

        stored_messages = list(result.get("messages") or messages)
        stored_messages.append({"role": "assistant", "content": reply})
        result["messages"] = stored_messages
        await save_campaign_state(user_id, workflow_id, result)

        workflow_data = workflow_from_state(result)
        brief_data = brief_from_state(result)
        return ChatProcessResult(
            message=reply,
            workflow=workflow_data,
            campaign_brief=brief_data,
            brief_status=result.get("brief_status"),
        )


chat_service = ChatService()
