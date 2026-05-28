from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel

from app.models.common import utc_now
from app.schemas.workflow import WorkflowDefinition


class WorkflowVersion(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    workflow_id: str = Field(..., min_length=1)
    version: int = Field(..., ge=1)
    definition: WorkflowDefinition
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "workflow_versions"
        indexes = [
            IndexModel(
                [("workflow_id", 1), ("version", -1)],
                name="idx_workflow_versions_workflow_version",
            ),
            IndexModel(
                [("workflow_id", 1), ("version", 1)],
                unique=True,
                name="idx_workflow_versions_workflow_version_unique",
            ),
        ]
