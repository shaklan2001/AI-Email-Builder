from uuid import uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel

from app.models.common import TimestampMixin
from app.schemas.campaign_brief import CampaignBriefData
from app.schemas.enums import CampaignStatus


class Campaign(TimestampMixin, Document):
    id: str = Field(default_factory=lambda: uuid4().hex)
    user_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=200)
    status: CampaignStatus = CampaignStatus.DRAFT
    workflow_id: str | None = None
    brief: CampaignBriefData | None = None

    class Settings:
        name = "campaigns"
        indexes = [
            IndexModel(
                [("user_id", 1), ("status", 1)],
                name="idx_campaigns_user_status",
            ),
            IndexModel(
                [("user_id", 1), ("updated_at", -1)],
                name="idx_campaigns_user_updated",
            ),
        ]
