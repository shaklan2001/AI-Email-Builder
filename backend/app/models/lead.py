from beanie import Document, PydanticObjectId
from pydantic import EmailStr, Field
from pymongo import IndexModel

from app.models.common import TimestampMixin
from app.schemas.enums import LeadStatus


class Lead(TimestampMixin, Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    campaign_id: str = Field(..., min_length=1)
    workflow_id: str | None = None
    email: EmailStr
    name: str | None = Field(default=None, max_length=200)
    status: LeadStatus = LeadStatus.PENDING

    class Settings:
        name = "leads"
        indexes = [
            IndexModel(
                [("campaign_id", 1), ("email", 1)],
                unique=True,
                name="idx_leads_campaign_email",
            ),
            IndexModel(
                [("campaign_id", 1), ("status", 1)],
                name="idx_leads_campaign_status",
            ),
            IndexModel(
                [("workflow_id", 1)],
                sparse=True,
                name="idx_leads_workflow_id",
            ),
        ]
