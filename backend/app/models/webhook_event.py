from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WebhookEventType = Literal["delivered", "opened", "clicked", "replied", "bounced"]


class WebhookEvent(BaseModel):
    id: str = Field(..., min_length=1)
    event_id: str = Field(..., min_length=1)
    event_type: WebhookEventType
    timestamp: datetime
    recipient: str = Field(..., min_length=1)
    workflow_id: str | None = None
    resend_email_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    processed: bool = False
    created_at: datetime
