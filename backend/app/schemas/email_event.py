from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.enums import EmailEventType


class EmailEventBase(BaseModel):
    event_id: str = Field(..., min_length=1)
    event_type: EmailEventType
    campaign_id: str | None = None
    workflow_id: str | None = None
    lead_id: str | None = None
    resend_message_id: str | None = None
    recipient_email: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    processed: bool = False


class EmailEventCreate(EmailEventBase):
    pass


class EmailEventRead(EmailEventBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
