from pydantic import BaseModel, Field, model_validator

from app.schemas.requests import CampaignBriefFieldData, WorkflowDefinitionData


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    thread_id: str | None = Field(default=None, alias="threadId")
    workflow_id: str | None = Field(default=None, alias="workflowId")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def require_thread_id(self) -> "ChatMessageRequest":
        if not self.resolved_thread_id():
            raise ValueError("threadId or workflowId is required")
        return self

    def resolved_thread_id(self) -> str | None:
        return self.thread_id or self.workflow_id


class ChatResetRequest(BaseModel):
    thread_id: str | None = Field(default=None, alias="threadId")
    workflow_id: str | None = Field(default=None, alias="workflowId")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def require_thread_id(self) -> "ChatResetRequest":
        if not self.resolved_thread_id():
            raise ValueError("threadId or workflowId is required")
        return self

    def resolved_thread_id(self) -> str | None:
        return self.thread_id or self.workflow_id


class ChatThreadMessageData(BaseModel):
    role: str
    content: str


class ChatResponseData(BaseModel):
    message: str = ""
    stage: str
    campaign_id: str | None = Field(default=None, alias="campaignId")
    campaign_brief: CampaignBriefFieldData | None = Field(default=None, alias="campaignBrief")
    workflow_preview: WorkflowDefinitionData | None = Field(default=None, alias="workflowPreview")
    brief_status: str | None = Field(default=None, alias="briefStatus")
    review_status: str | None = Field(default=None, alias="reviewStatus")
    approval_status: str | None = Field(default=None, alias="approvalStatus")
    activation_allowed: bool = Field(default=False, alias="activationAllowed")

    model_config = {"populate_by_name": True}


class ChatThreadData(BaseModel):
    thread_id: str = Field(..., alias="threadId")
    campaign_id: str | None = Field(default=None, alias="campaignId")
    messages: list[ChatThreadMessageData] = Field(default_factory=list)
    stage: str
    campaign_brief: CampaignBriefFieldData | None = Field(default=None, alias="campaignBrief")
    workflow_preview: WorkflowDefinitionData | None = Field(default=None, alias="workflowPreview")
    brief_status: str | None = Field(default=None, alias="briefStatus")
    review_status: str | None = Field(default=None, alias="reviewStatus")
    approval_status: str | None = Field(default=None, alias="approvalStatus")
    activation_allowed: bool = Field(default=False, alias="activationAllowed")

    model_config = {"populate_by_name": True}
