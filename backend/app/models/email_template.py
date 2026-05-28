from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel

from app.models.common import utc_now


class EmailTemplate(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    workflow_id: str = Field(..., min_length=1)
    step_id: str = Field(..., min_length=1)
    version: int = Field(..., ge=1)
    subject: str = Field(..., min_length=1)
    html_content: str = Field(..., min_length=1)
    plain_text_content: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "email_templates"
        indexes = [
            IndexModel(
                [("workflow_id", 1), ("step_id", 1), ("version", -1)],
                name="idx_templates_workflow_step_version",
            ),
            IndexModel(
                [("workflow_id", 1)],
                name="idx_templates_workflow",
            ),
        ]
