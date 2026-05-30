from dataclasses import dataclass

from app.core.workflow_ids import assert_valid_workflow_id
from app.langgraph.state import ConversationState
from app.repositories.conversation_repository import conversation_repository
from app.repositories.workflow_repository import workflow_repository
from app.schemas.chat import ChatResponseData, ChatThreadData, ChatThreadMessageData
from app.services.conversation_stage import resolve_stage_value
from app.services.conversation_state_service import empty_conversation_state
from app.services.workflow_state_response import brief_from_state, workflow_from_state


@dataclass
class ChatThreadResult:
    data: ChatThreadData
    found: bool


def _messages_from_state(state: ConversationState) -> list[ChatThreadMessageData]:
    rows: list[ChatThreadMessageData] = []
    for item in state.get("messages") or []:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if isinstance(role, str) and isinstance(content, str):
            rows.append(ChatThreadMessageData(role=role, content=content))
    return rows


def _response_from_state(
    *,
    thread_id: str,
    state: ConversationState,
    message: str = "",
) -> ChatResponseData:
    workflow_preview = workflow_from_state(state)
    campaign_brief = brief_from_state(state)
    return ChatResponseData(
        message=message,
        stage=resolve_stage_value(state),
        campaign_id=str(state.get("campaign_id") or state.get("workflow_id") or thread_id),
        campaign_brief=campaign_brief,
        workflow_preview=workflow_preview,
        brief_status=state.get("brief_status"),
        review_status=state.get("review_status"),
        approval_status=state.get("approval_status"),
        activation_allowed=state.get("review_status") == "approved",
    )


def _thread_from_state(*, thread_id: str, state: ConversationState) -> ChatThreadData:
    response = _response_from_state(thread_id=thread_id, state=state)
    return ChatThreadData(
        thread_id=thread_id,
        campaign_id=str(state.get("campaign_id") or state.get("workflow_id") or thread_id),
        messages=_messages_from_state(state),
        stage=response.stage,
        campaign_brief=response.campaign_brief,
        workflow_preview=response.workflow_preview,
        brief_status=response.brief_status,
        review_status=response.review_status,
        approval_status=response.approval_status,
        activation_allowed=response.activation_allowed,
    )


class ChatThreadService:
    async def _assert_thread_access(self, *, user_id: str, thread_id: str) -> bool:
        assert_valid_workflow_id(thread_id)
        record = await workflow_repository.get_by_id(user_id, thread_id)
        return record is not None

    async def get_thread(self, *, user_id: str, thread_id: str) -> ChatThreadResult | None:
        if not await self._assert_thread_access(user_id=user_id, thread_id=thread_id):
            return None

        state = await conversation_repository.get_conversation_state(user_id, thread_id)
        if state is None:
            empty = empty_conversation_state(user_id=user_id, workflow_id=thread_id)
            return ChatThreadResult(
                data=_thread_from_state(thread_id=thread_id, state=empty),
                found=True,
            )

        return ChatThreadResult(
            data=_thread_from_state(thread_id=thread_id, state=state),
            found=True,
        )

    async def reset_thread(self, *, user_id: str, thread_id: str) -> ChatThreadResult | None:
        if not await self._assert_thread_access(user_id=user_id, thread_id=thread_id):
            return None

        from app.services.persistence import save_conversation_state

        empty = empty_conversation_state(user_id=user_id, workflow_id=thread_id)
        await save_conversation_state(user_id, thread_id, empty)
        return ChatThreadResult(
            data=_thread_from_state(thread_id=thread_id, state=empty),
            found=True,
        )

    def build_response(
        self,
        *,
        thread_id: str,
        state: ConversationState,
        message: str,
    ) -> ChatResponseData:
        return _response_from_state(thread_id=thread_id, state=state, message=message)

chat_thread_service = ChatThreadService()
