from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WorkflowRunStatus = Literal["queued", "running", "waiting", "completed", "failed"]


class WorkflowRun(BaseModel):
    id: str = Field(..., min_length=1)
    workflow_id: str = Field(..., min_length=1)
    recipient_id: str = Field(..., min_length=1)
    current_step: str = Field(..., min_length=1)
    status: WorkflowRunStatus
    next_execution_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
