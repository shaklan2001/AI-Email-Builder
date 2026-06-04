from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel

from app.models.common import utc_now
from app.schemas.enums import EmailEventType


class EmailEvent(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    event_id: str = Field(..., min_length=1)
    event_type: EmailEventType
    campaign_id: str | None = None
    workflow_id: str | None = None
    lead_id: str | None = None
    resend_message_id: str | None = None
    recipient_email: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    processed: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "email_events"
        indexes = [
            IndexModel(
                [("event_id", 1)],
                unique=True,
                name="idx_email_events_event_id",
            ),
            IndexModel(
                [("workflow_id", 1), ("event_type", 1)],
                name="idx_email_events_workflow_type",
            ),
            IndexModel(
                [("processed", 1), ("created_at", 1)],
                name="idx_email_events_processed",
            ),
            IndexModel(
                [("resend_message_id", 1)],
                sparse=True,
                name="idx_email_events_resend_message_id",
            ),
        ]
