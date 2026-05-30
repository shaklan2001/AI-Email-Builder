from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.enums import ThreadMessageKind, ThreadMessageRole


class ThreadMessage(BaseModel):
    role: ThreadMessageRole
    message_kind: ThreadMessageKind
    content: str = Field(..., min_length=1)
    sent_at: datetime


class ConversationThreadBase(BaseModel):
    campaign_id: str = Field(..., min_length=1)
    lead_id: str = Field(..., min_length=1)
    workflow_id: str | None = None
    messages: list[ThreadMessage] = Field(default_factory=list)


class ConversationThreadCreate(ConversationThreadBase):
    pass


class ConversationThreadUpdate(BaseModel):
    workflow_id: str | None = None
    messages: list[ThreadMessage] | None = None


class ConversationThreadRead(ConversationThreadBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
