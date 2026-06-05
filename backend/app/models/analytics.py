from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowAnalytics(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    replied: int = 0
    failed: int = 0
    bounced: int = 0
    updated_at: datetime
