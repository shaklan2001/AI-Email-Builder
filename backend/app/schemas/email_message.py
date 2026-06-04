from datetime import datetime

from pydantic import BaseModel, Field


class EmailMessageRecordData(BaseModel):
    id: str
    resend_message_id: str
    workflow_id: str
    lead_id: str
    step_id: str | None = None
    sent: bool = True
    delivered: bool = False
    opened: bool = False
    clicked: bool = False
    replied: bool = False
    failed: bool = False
    created_at: datetime
    updated_at: datetime


class SendEmailResult(BaseModel):
    resend_message_id: str = Field(..., alias="resendMessageId")
    workflow_id: str = Field(..., alias="workflowId")
    lead_id: str = Field(..., alias="leadId")
    step_id: str | None = Field(default=None, alias="stepId")

    model_config = {"populate_by_name": True}


class BulkSendEmailResult(BaseModel):
    sent_count: int = Field(..., alias="sentCount")
    failed_count: int = Field(..., alias="failedCount")
    results: list[SendEmailResult]
    message_ids: list[str] = Field(default_factory=list, alias="messageIds")

    model_config = {"populate_by_name": True}
