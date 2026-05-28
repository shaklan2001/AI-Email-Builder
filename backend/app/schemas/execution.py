from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.enums import ExecutionStatus


class ExecutionBase(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    lead_id: str = Field(..., min_length=1)
    current_step_id: str = Field(..., min_length=1)
    status: ExecutionStatus = ExecutionStatus.QUEUED
    next_execution_at: datetime | None = None


class ExecutionCreate(ExecutionBase):
    pass


class ExecutionUpdate(BaseModel):
    current_step_id: str | None = Field(default=None, min_length=1)
    status: ExecutionStatus | None = None
    next_execution_at: datetime | None = None


class ExecutionRead(ExecutionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
