from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class WorkflowCreate(WorkflowBase):
    user_id: str = Field(..., min_length=1)
    campaign_id: str = Field(..., min_length=1)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    active_version: int | None = Field(default=None, ge=1)


class WorkflowRead(WorkflowBase):
    id: str
    user_id: str
    campaign_id: str
    active_version: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
