from datetime import datetime

from pydantic import BaseModel, Field


class EmailTemplateBase(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    step_id: str = Field(..., min_length=1)
    version: int = Field(..., ge=1)
    subject: str = Field(..., min_length=1)
    html_content: str = Field(..., min_length=1)
    plain_text_content: str = Field(..., min_length=1)


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateRead(EmailTemplateBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
