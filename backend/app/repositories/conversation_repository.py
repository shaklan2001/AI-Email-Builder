from datetime import UTC, datetime
from typing import Any

from app.core.database import get_database
from app.langgraph.state import ConversationState
from app.services.conversation_state_service import sanitize_loaded_state


class ConversationRepository:
    COLLECTION = "conversations"

    def _persisted_fields(self) -> tuple[str, ...]:
        return (
            "messages",
            "campaign_brief",
            "workflow",
            "email_templates",
            "recipients",
            "missing_fields",
            "current_stage",
            "campaign_name",
            "business_goal",
            "product_info",
            "audience",
            "tone",
            "cta",
            "attachments",
            "competitors",
            "landing_page",
            "product_image",
            "follow_up_strategy",
            "follow_up_delay",
            "reply_strategy",
            "brief_status",
            "brief_approved",
            "review_status",
            "regenerate_workflow",
            "skipped_fields",
        )

    def _doc_to_state(self, doc: dict[str, Any]) -> ConversationState:
        state: ConversationState = {
            "workflow_id": str(doc["workflow_id"]),
            "user_id": str(doc["user_id"]),
            "thread_id": str(doc.get("thread_id") or doc["workflow_id"]),
        }
        for field in self._persisted_fields():
            if field in doc:
                state[field] = doc[field]  # type: ignore[literal-required]
        return sanitize_loaded_state(state)

    def _state_to_doc(
        self,
        user_id: str,
        workflow_id: str,
        state: ConversationState,
    ) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "user_id": user_id,
            "workflow_id": workflow_id,
            "thread_id": workflow_id,
            "updated_at": datetime.now(UTC),
        }
        for field in self._persisted_fields():
            if field in state:
                doc[field] = state[field]
        return doc

    async def get_conversation_state(
        self,
        user_id: str,
        workflow_id: str,
    ) -> ConversationState | None:
        doc = await get_database()[self.COLLECTION].find_one(
            {"user_id": user_id, "workflow_id": workflow_id},
        )
        if doc is None:
            return None
        return self._doc_to_state(doc)

    async def get_campaign_state(
        self,
        user_id: str,
        workflow_id: str,
    ) -> ConversationState | None:
        return await self.get_conversation_state(user_id, workflow_id)

    async def upsert_conversation_state(
        self,
        user_id: str,
        workflow_id: str,
        state: ConversationState,
    ) -> None:
        now = datetime.now(UTC)
        update_doc = self._state_to_doc(user_id, workflow_id, state)
        await get_database()[self.COLLECTION].update_one(
            {"user_id": user_id, "workflow_id": workflow_id},
            {
                "$set": update_doc,
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    async def upsert_campaign_state(
        self,
        user_id: str,
        workflow_id: str,
        state: ConversationState,
    ) -> None:
        await self.upsert_conversation_state(user_id, workflow_id, state)


conversation_repository = ConversationRepository()
