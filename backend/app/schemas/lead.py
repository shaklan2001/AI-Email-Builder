from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.enums import LeadStatus


class LeadBase(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=200)
    status: LeadStatus = LeadStatus.PENDING


class LeadCreate(LeadBase):
    campaign_id: str = Field(..., min_length=1)
    workflow_id: str | None = None


class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    status: LeadStatus | None = None
    workflow_id: str | None = None


class LeadRead(LeadBase):
    id: str
    campaign_id: str
    workflow_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
