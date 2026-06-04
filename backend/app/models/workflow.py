from uuid import uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel

from app.models.common import TimestampMixin


class Workflow(TimestampMixin, Document):
    id: str = Field(default_factory=lambda: uuid4().hex)
    user_id: str = Field(..., min_length=1)
    campaign_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=200)
    active_version: int | None = Field(default=None, ge=1)

    class Settings:
        name = "workflows"
        indexes = [
            IndexModel(
                [("campaign_id", 1)],
                name="idx_workflows_campaign_id",
            ),
            IndexModel(
                [("user_id", 1), ("updated_at", -1)],
                name="idx_workflows_user_updated",
            ),
        ]
