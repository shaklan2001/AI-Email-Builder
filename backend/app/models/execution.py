from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel

from app.models.common import TimestampMixin
from app.schemas.enums import ExecutionStatus


class Execution(TimestampMixin, Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    workflow_id: str = Field(..., min_length=1)
    lead_id: str = Field(..., min_length=1)
    current_step_id: str = Field(..., min_length=1)
    status: ExecutionStatus = ExecutionStatus.QUEUED
    next_execution_at: datetime | None = None

    class Settings:
        name = "executions"
        indexes = [
            IndexModel(
                [("next_execution_at", 1), ("status", 1)],
                name="idx_executions_due_execution",
            ),
            IndexModel(
                [("workflow_id", 1), ("lead_id", 1)],
                unique=True,
                name="idx_executions_workflow_lead",
            ),
            IndexModel(
                [("workflow_id", 1), ("status", 1)],
                name="idx_executions_workflow_status",
            ),
        ]
