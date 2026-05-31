from datetime import UTC, datetime
from typing import Any

from app.core.database import get_database
from app.langgraph.state import CampaignState


class ConversationRepository:
    COLLECTION = "conversations"

    def _campaign_fields(self) -> tuple[str, ...]:
        return (
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
            "reply_strategy",
            "brief_status",
            "brief_approved",
            "campaign_brief",
            "workflow",
            "skipped_fields",
        )

    def _doc_to_state(self, doc: dict[str, Any]) -> CampaignState:
        state: CampaignState = {
            "workflow_id": str(doc["workflow_id"]),
            "user_id": str(doc["user_id"]),
        }
        for field in self._campaign_fields():
            if field in doc:
                state[field] = doc[field]  # type: ignore[literal-required]
        return state

    def _state_to_doc(self, user_id: str, workflow_id: str, state: CampaignState) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "user_id": user_id,
            "workflow_id": workflow_id,
            "updated_at": datetime.now(UTC),
        }
        for field in self._campaign_fields():
            if field in state:
                doc[field] = state[field]
        return doc

    async def get_campaign_state(
        self,
        user_id: str,
        workflow_id: str,
    ) -> CampaignState | None:
        doc = await get_database()[self.COLLECTION].find_one(
            {"user_id": user_id, "workflow_id": workflow_id},
        )
        if doc is None:
            return None
        return self._doc_to_state(doc)

    async def upsert_campaign_state(
        self,
        user_id: str,
        workflow_id: str,
        state: CampaignState,
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


conversation_repository = ConversationRepository()
