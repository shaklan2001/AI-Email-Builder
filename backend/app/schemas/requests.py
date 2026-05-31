from typing import Any

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    workflow_id: str = Field(..., min_length=1, alias="workflowId")

    model_config = {"populate_by_name": True}


class EmailBodyVersionData(BaseModel):
    subject: str
    html_content: str = Field(..., alias="htmlContent")
    plain_text_content: str = Field(..., alias="plainTextContent")

    model_config = {"populate_by_name": True}


class GeneratedEmailData(BaseModel):
    subject: str
    html_content: str = Field(..., alias="htmlContent")
    plain_text_content: str = Field(..., alias="plainTextContent")
    ai_generated_version: EmailBodyVersionData | None = Field(
        default=None, alias="aiGeneratedVersion"
    )
    final_user_version: EmailBodyVersionData | None = Field(
        default=None, alias="finalUserVersion"
    )
    user_edited: bool = Field(default=False, alias="userEdited")

    model_config = {"populate_by_name": True}


class UpdateWorkflowEmailRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    html_content: str = Field(..., min_length=1, alias="htmlContent")
    plain_text_content: str = Field(..., min_length=1, alias="plainTextContent")

    model_config = {"populate_by_name": True}


class WorkflowStepData(BaseModel):
    id: str
    type: str
    name: str | None = None
    days: int | None = None
    condition: str | None = None
    branch: str | None = None
    email: GeneratedEmailData | None = None


class WorkflowDefinitionData(BaseModel):
    workflow_type: str | None = Field(default=None, alias="workflowType")
    steps: list[WorkflowStepData] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class CampaignBriefFieldData(BaseModel):
    campaign_name: str | None = Field(default=None, alias="campaignName")
    business_goal: str | None = Field(default=None, alias="businessGoal")
    audience: str | None = None
    product_info: str | None = Field(default=None, alias="productInfo")
    tone: str | None = None
    cta: str | None = None
    attachments: str | None = None
    landing_page: str | None = Field(default=None, alias="landingPage")
    follow_up_strategy: str | None = Field(default=None, alias="followUpStrategy")
    reply_strategy: str | None = Field(default=None, alias="replyStrategy")

    model_config = {"populate_by_name": True}


class ChatMessageData(BaseModel):
    message: str
    workflow: WorkflowDefinitionData | None = None
    campaign_brief: CampaignBriefFieldData | None = Field(default=None, alias="campaignBrief")
    brief_status: str | None = Field(default=None, alias="briefStatus")

    model_config = {"populate_by_name": True}


class CampaignDraftData(BaseModel):
    campaign_name: str | None = Field(default=None, alias="campaignName")
    business_goal: str | None = Field(default=None, alias="businessGoal")
    product_info: str | None = Field(default=None, alias="productInfo")
    audience: str | None = None
    tone: str | None = None
    cta: str | None = None
    landing_page: str | None = Field(default=None, alias="landingPage")
    product_image: str | None = Field(default=None, alias="productImage")
    follow_up_strategy: str | None = Field(default=None, alias="followUpStrategy")
    reply_strategy: str | None = Field(default=None, alias="replyStrategy")

    model_config = {"populate_by_name": True}


class WorkflowSessionData(BaseModel):
    messages: list[dict[str, str]] = Field(default_factory=list)
    campaign_draft: CampaignDraftData = Field(default_factory=CampaignDraftData, alias="campaignDraft")
    campaign_brief: CampaignBriefFieldData | None = Field(default=None, alias="campaignBrief")
    brief_status: str | None = Field(default=None, alias="briefStatus")
    workflow: WorkflowDefinitionData | None = None
    generated_emails: list[GeneratedEmailData] = Field(default_factory=list, alias="generatedEmails")

    model_config = {"populate_by_name": True}


class CreateWorkflowRequest(BaseModel):
    conversation_id: str | None = None
    name: str | None = None


class WorkflowData(BaseModel):
    id: str
    name: str
    status: str
    created_at: str


class RecipientUploadData(BaseModel):
    valid_count: int
    invalid_count: int
    valid_emails: list[str]
    invalid_rows: list[dict[str, str]]


class ReviewRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1)


class ReviewData(BaseModel):
    workflow_summary: dict[str, Any]
    email_summary: dict[str, Any]
    recipient_count: int
    schedule_summary: dict[str, Any]


class SendEmailRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1, alias="workflowId")

    model_config = {"populate_by_name": True}


class EmailSendStatusData(BaseModel):
    status: str
    message_id: str | None = None
    recipient_count: int
    step_id: str | None = None
