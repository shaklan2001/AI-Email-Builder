from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.workflow import WorkflowDefinition


class WorkflowVersionBase(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    version: int = Field(..., ge=1)
    definition: WorkflowDefinition


class WorkflowVersionCreate(WorkflowVersionBase):
    pass


class WorkflowVersionRead(WorkflowVersionBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
