"""Read conversation threads for workflow preview and lead detail views."""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from app.repositories.conversation_thread_repository import conversation_thread_repository
from app.repositories.workflow_repository import workflow_repository


class ConversationThreadMessageData(BaseModel):
    id: str
    type: str = Field(..., description="agent_message | prospect_reply | agent_response")
    content: str


class ConversationThreadSummaryData(BaseModel):
    lead_email: str = Field(..., alias="leadEmail")
    messages: list[ConversationThreadMessageData] = Field(default_factory=list)
    auto_reply_count: int = Field(default=0, alias="autoReplyCount")
    human_review_required: bool = Field(default=False, alias="humanReviewRequired")

    model_config = {"populate_by_name": True}


def _message_id(message: dict[str, object], index: int) -> str:
    sent_at = message.get("sent_at")
    if isinstance(sent_at, datetime):
        return f"{sent_at.isoformat()}-{index}"
    return f"msg-{index}"


def _doc_to_summary(doc: dict[str, object]) -> ConversationThreadSummaryData:
    lead_id = str(doc.get("lead_id") or "")
    raw_messages = doc.get("messages")
    messages: list[ConversationThreadMessageData] = []
    if isinstance(raw_messages, list):
        for index, item in enumerate(raw_messages):
            if not isinstance(item, dict):
                continue
            kind = item.get("message_kind") or item.get("type")
            content = item.get("content")
            if not isinstance(kind, str) or not isinstance(content, str) or not content.strip():
                continue
            messages.append(
                ConversationThreadMessageData(
                    id=_message_id(item, index),
                    type=kind,
                    content=content.strip(),
                ),
            )

    return ConversationThreadSummaryData(
        leadEmail=lead_id,
        messages=messages,
        autoReplyCount=int(doc.get("auto_reply_count") or 0),
        humanReviewRequired=bool(doc.get("human_review_required", False)),
    )


class ConversationThreadsService:
    async def list_for_workflow(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> list[ConversationThreadSummaryData]:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        docs = await conversation_thread_repository.list_by_workflow(workflow_id)
        return [_doc_to_summary(doc) for doc in docs if doc.get("messages")]

    async def preview_thread(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> ConversationThreadSummaryData | None:
        threads = await self.list_for_workflow(user_id=user_id, workflow_id=workflow_id)
        if not threads:
            return None
        return max(threads, key=lambda t: len(t.messages))


conversation_threads_service = ConversationThreadsService()
