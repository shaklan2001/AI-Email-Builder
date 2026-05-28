"""Per-lead conversation threads for auto-reply tracking."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import get_database
from app.repositories.lead_repository import LeadRepository
from app.schemas.enums import ThreadMessageKind, ThreadMessageRole


class ConversationThreadRepository:
    COLLECTION = "conversation_threads"
    MAX_AUTO_REPLIES = LeadRepository.MAX_AUTO_REPLIES

    async def get_thread(
        self,
        *,
        campaign_id: str,
        lead_email: str,
    ) -> dict[str, Any] | None:
        doc = await get_database()[self.COLLECTION].find_one(
            {"campaign_id": campaign_id, "lead_id": lead_email.lower()},
        )
        return doc

    async def append_message(
        self,
        *,
        campaign_id: str,
        workflow_id: str,
        lead_email: str,
        role: ThreadMessageRole | str,
        message_kind: ThreadMessageKind | str,
        content: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        lead_id = lead_email.lower()
        message = {
            "role": role.value if isinstance(role, ThreadMessageRole) else str(role),
            "message_kind": (
                message_kind.value
                if isinstance(message_kind, ThreadMessageKind)
                else str(message_kind)
            ),
            "content": content.strip(),
            "sent_at": now,
        }

        existing = await self.get_thread(campaign_id=campaign_id, lead_email=lead_id)
        if existing is not None:
            result = await get_database()[self.COLLECTION].find_one_and_update(
                {"_id": existing["_id"]},
                {
                    "$push": {"messages": message},
                    "$set": {"updated_at": now, "workflow_id": workflow_id},
                },
                return_document=True,
            )
            assert result is not None
            return result

        doc_id = str(uuid4())
        doc: dict[str, Any] = {
            "_id": doc_id,
            "campaign_id": campaign_id,
            "workflow_id": workflow_id,
            "lead_id": lead_id,
            "messages": [message],
            "auto_reply_count": 0,
            "human_review_required": False,
            "created_at": now,
            "updated_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return doc

    async def increment_auto_reply_count(
        self,
        *,
        campaign_id: str,
        lead_email: str,
    ) -> tuple[int, bool]:
        now = datetime.now(UTC)
        lead_id = lead_email.lower()
        doc = await get_database()[self.COLLECTION].find_one_and_update(
            {"campaign_id": campaign_id, "lead_id": lead_id},
            {
                "$inc": {"auto_reply_count": 1},
                "$set": {"updated_at": now},
            },
            return_document=True,
        )
        if doc is None:
            return 0, False
        count = int(doc.get("auto_reply_count") or 0)
        human_required = count >= self.MAX_AUTO_REPLIES
        if human_required and not doc.get("human_review_required"):
            await get_database()[self.COLLECTION].update_one(
                {"_id": doc["_id"]},
                {"$set": {"human_review_required": True, "updated_at": now}},
            )
        return count, human_required

    async def is_human_review_required(
        self,
        *,
        campaign_id: str,
        lead_email: str,
    ) -> bool:
        doc = await self.get_thread(campaign_id=campaign_id, lead_email=lead_email)
        if doc is None:
            return False
        if bool(doc.get("human_review_required")):
            return True
        return int(doc.get("auto_reply_count") or 0) >= self.MAX_AUTO_REPLIES

    async def get_messages(
        self,
        *,
        campaign_id: str,
        lead_email: str,
    ) -> list[dict[str, Any]]:
        doc = await self.get_thread(campaign_id=campaign_id, lead_email=lead_email)
        if doc is None:
            return []
        messages = doc.get("messages")
        if not isinstance(messages, list):
            return []
        return [m for m in messages if isinstance(m, dict)]

    async def list_by_workflow(self, workflow_id: str) -> list[dict[str, Any]]:
        cursor = get_database()[self.COLLECTION].find(
            {
                "$or": [
                    {"workflow_id": workflow_id},
                    {"campaign_id": workflow_id},
                ],
            },
        ).sort("updated_at", -1)
        docs = await cursor.to_list(length=50)
        return docs


conversation_thread_repository = ConversationThreadRepository()
