from datetime import UTC, datetime
from typing import Any

from app.core.database import get_database
from app.langgraph.state import CampaignState, ConversationState

# All ConversationState fields persisted to MongoDB (single source of truth).
PERSISTED_STATE_FIELDS: tuple[str, ...] = (
    "campaign_id",
    "thread_id",
    "messages",
    "campaign_name",
    "business_goal",
    "product_info",
    "audience",
    "tone",
    "cta",
    "attachments",
    "landing_page",
    "product_image",
    "follow_up_strategy",
    "follow_up_delay",
    "wants_follow_up",
    "email_length",
    "email_length_words",
    "reply_strategy",
    "skipped_fields",
    "brief_status",
    "brief_approved",
    "campaign_brief",
    "workflow",
    "email_templates",
    "recipients",
    "missing_fields",
    "current_stage",
    "approval_status",
    "review_status",
    "regenerate_workflow",
    "leads",
    "conversation_threads",
    "reply_intent",
    "tool_calls",
    "lead_status",
    "generated_responses",
)


class ConversationRepository:
    COLLECTION = "conversations"

    def _doc_to_state(self, doc: dict[str, Any]) -> ConversationState:
        workflow_id = str(doc["workflow_id"])
        state: ConversationState = {
            "workflow_id": workflow_id,
            "user_id": str(doc["user_id"]),
            "campaign_id": str(doc.get("campaign_id") or workflow_id),
            "thread_id": str(doc.get("thread_id") or workflow_id),
        }
        for field in PERSISTED_STATE_FIELDS:
            if field in doc and field not in ("campaign_id", "thread_id"):
                state[field] = doc[field]  # type: ignore[literal-required]
        return state

    def _state_to_doc(
        self,
        user_id: str,
        workflow_id: str,
        state: ConversationState,
    ) -> dict[str, Any]:
        campaign_id = str(state.get("campaign_id") or workflow_id)
        thread_id = str(state.get("thread_id") or workflow_id)
        doc: dict[str, Any] = {
            "user_id": user_id,
            "workflow_id": workflow_id,
            "campaign_id": campaign_id,
            "thread_id": thread_id,
            "updated_at": datetime.now(UTC),
        }
        for field in PERSISTED_STATE_FIELDS:
            if field in ("campaign_id", "thread_id"):
                continue
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

    async def get_campaign_state(
        self,
        user_id: str,
        workflow_id: str,
    ) -> CampaignState | None:
        return await self.get_conversation_state(user_id, workflow_id)

    async def upsert_campaign_state(
        self,
        user_id: str,
        workflow_id: str,
        state: CampaignState,
    ) -> None:
        await self.upsert_conversation_state(user_id, workflow_id, state)


conversation_repository = ConversationRepository()
