from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.campaign_brief import CampaignBriefData
from app.schemas.enums import CampaignStatus


class CampaignBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    status: CampaignStatus = CampaignStatus.DRAFT


class CampaignCreate(CampaignBase):
    user_id: str = Field(..., min_length=1)
    workflow_id: str | None = None
    brief: CampaignBriefData | None = None


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: CampaignStatus | None = None
    workflow_id: str | None = None
    brief: CampaignBriefData | None = None


class CampaignRead(CampaignBase):
    id: str
    user_id: str
    workflow_id: str | None = None
    brief: CampaignBriefData | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
