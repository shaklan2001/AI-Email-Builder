from dataclasses import dataclass

from app.langgraph.graph import get_campaign_graph
from app.langgraph.state import MessageDict
from app.providers.llm.base import LLMProviderError
from app.repositories.conversation_repository import conversation_repository
from app.schemas.chat import ChatResponseData
from app.schemas.requests import CampaignBriefFieldData, WorkflowDefinitionData
from app.services.brief_actions import parse_brief_user_action
from app.core.workflow_ids import assert_valid_workflow_id
from app.services.chat_thread_service import chat_thread_service
from app.services.conversation_response import build_brief_edit_reply
from app.services.conversation_stage import _has_workflow_steps
from app.services.conversation_state_service import empty_conversation_state
from app.services.persistence import save_conversation_state
from app.services.review_actions import parse_review_user_action
from app.services.review_service import (
    apply_review_approve,
    apply_review_edit_campaign,
    apply_review_regenerate_workflow,
)

_LLM_UNAVAILABLE_REPLY = (
    "I'm having trouble reaching the AI service right now. Please try again in a moment."
)


@dataclass
class ChatProcessResult:
    message: str
    stage: str
    workflow_preview: WorkflowDefinitionData | None
    campaign_brief: CampaignBriefFieldData | None = None
    brief_status: str | None = None
    review_status: str | None = None
    activation_allowed: bool = False


def _to_process_result(response: ChatResponseData) -> ChatProcessResult:
    return ChatProcessResult(
        message=response.message,
        stage=response.stage,
        workflow_preview=response.workflow_preview,
        campaign_brief=response.campaign_brief,
        brief_status=response.brief_status,
        review_status=response.review_status,
        activation_allowed=response.activation_allowed,
    )


class ChatService:
    async def process_message(
        self,
        *,
        user_id: str,
        thread_id: str,
        message: str,
    ) -> ChatProcessResult:
        assert_valid_workflow_id(thread_id)
        state = await conversation_repository.get_conversation_state(user_id, thread_id)
        if state is None:
            state = empty_conversation_state(user_id=user_id, workflow_id=thread_id)

        messages: list[MessageDict] = list(state.get("messages") or [])
        messages.append({"role": "user", "content": message})
        state["messages"] = messages

        review_action = None
        if _has_workflow_steps(state.get("workflow")) and state.get("review_status") != "approved":
            review_action = parse_review_user_action(message)

        brief_action = None
        if review_action is None and state.get("brief_status") == "pending_approval":
            brief_action = parse_brief_user_action(message)
            if brief_action == "approve":
                state["brief_approved"] = True
                state["brief_status"] = "approved"
            elif brief_action == "edit":
                state["brief_approved"] = False
                state["brief_status"] = "editing"
                state["campaign_brief"] = None
        elif review_action is None and state.get("brief_status") == "editing" and parse_brief_user_action(message) is None:
            state["brief_status"] = None
            state["campaign_brief"] = None

        skip_graph = False
        preset_reply: str | None = None

        if review_action == "approve":
            updates = apply_review_approve(state)
            state.update(updates)  # type: ignore[arg-type]
            skip_graph = True
            preset_reply = str(updates.get("assistant_reply", ""))
        elif review_action == "edit_campaign":
            updates = apply_review_edit_campaign(state)
            state.update(updates)  # type: ignore[arg-type]
            skip_graph = True
            preset_reply = str(updates.get("assistant_reply", ""))
        elif review_action == "regenerate_workflow":
            updates = apply_review_regenerate_workflow(state)
            state.update(updates)  # type: ignore[arg-type]

        state = await save_conversation_state(user_id, thread_id, state)

        if skip_graph:
            reply = preset_reply or ""
            stored_messages: list[MessageDict] = list(state.get("messages") or messages)
            stored_messages.append({"role": "assistant", "content": reply})
            state["messages"] = stored_messages
            state["assistant_reply"] = reply
            state = await save_conversation_state(user_id, thread_id, state)
            return _to_process_result(
                chat_thread_service.build_response(
                    thread_id=thread_id,
                    state=state,
                    message=reply,
                ),
            )

        try:
            result = await get_campaign_graph().ainvoke(
                state,
                config={
                    "run_name": "campaign_graph",
                    "metadata": {
                        "user_id": user_id,
                        "thread_id": thread_id,
                        "workflow_id": thread_id,
                    },
                },
            )
        except LLMProviderError:
            return _to_process_result(
                chat_thread_service.build_response(
                    thread_id=thread_id,
                    state=state,
                    message=_LLM_UNAVAILABLE_REPLY,
                ),
            )

        result["regenerate_workflow"] = False
        result = await save_conversation_state(user_id, thread_id, result)
        reply = result.get("assistant_reply", "").strip()
        if brief_action == "edit":
            reply = build_brief_edit_reply()
            result["assistant_reply"] = reply
        if not reply:
            return _to_process_result(
                chat_thread_service.build_response(
                    thread_id=thread_id,
                    state=result,
                    message=_LLM_UNAVAILABLE_REPLY,
                ),
            )

        stored_messages: list[MessageDict] = list(result.get("messages") or messages)
        stored_messages.append({"role": "assistant", "content": reply})
        result["messages"] = stored_messages
        result = await save_conversation_state(user_id, thread_id, result)

        return _to_process_result(
            chat_thread_service.build_response(
                thread_id=thread_id,
                state=result,
                message=reply,
            ),
        )


chat_service = ChatService()
