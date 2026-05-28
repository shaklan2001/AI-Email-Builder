from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel

from app.models.common import TimestampMixin
from app.schemas.conversation_thread import ThreadMessage


class ConversationThread(TimestampMixin, Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    campaign_id: str = Field(..., min_length=1)
    lead_id: str = Field(..., min_length=1)
    workflow_id: str | None = None
    messages: list[ThreadMessage] = Field(default_factory=list)

    class Settings:
        name = "conversation_threads"
        indexes = [
            IndexModel(
                [("campaign_id", 1), ("lead_id", 1)],
                unique=True,
                name="idx_conversation_threads_campaign_lead",
            ),
            IndexModel(
                [("workflow_id", 1)],
                sparse=True,
                name="idx_conversation_threads_workflow_id",
            ),
            IndexModel(
                [("lead_id", 1), ("updated_at", -1)],
                name="idx_conversation_threads_lead_updated",
            ),
        ]
