from typing import Any, Literal

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
    value: int | None = None
    unit: str | None = None
    condition: str | None = None
    branch: str | None = None
    email: GeneratedEmailData | None = None


class FollowUpDelayData(BaseModel):
    value: int = Field(..., ge=1)
    unit: str

    model_config = {"populate_by_name": True}


class WorkflowDefinitionData(BaseModel):
    workflow_type: str | None = Field(default=None, alias="workflowType")
    follow_up_delay: FollowUpDelayData | None = Field(default=None, alias="followUpDelay")
    steps: list[WorkflowStepData] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class CampaignBriefFieldData(BaseModel):
    campaign_name: str | None = Field(default=None, alias="campaignName")
    product_info: str | None = Field(default=None, alias="productInfo")
    audience: str | None = None
    cta: str | None = None
    tone: str | None = None
    landing_page: str | None = Field(default=None, alias="landingPage")
    image_url: str | None = Field(default=None, alias="imageUrl")
    follow_up_delay: str | None = Field(default=None, alias="followUpDelay")
    reply_handling: str | None = Field(default=None, alias="replyHandling")
    tools_available: list[str] = Field(default_factory=list, alias="toolsAvailable")

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
    recipients: list[RecipientItemData] = Field(default_factory=list)
    recipient_counts: RecipientCountsData = Field(
        default_factory=lambda: RecipientCountsData(validCount=0, invalidCount=0),
        alias="recipientCounts",
    )

    model_config = {"populate_by_name": True}


class CreateWorkflowRequest(BaseModel):
    conversation_id: str | None = None
    name: str | None = None


class WorkflowData(BaseModel):
    id: str
    name: str
    status: str
    active_version: int | None = Field(default=None, alias="activeVersion")
    activated_at: str | None = Field(default=None, alias="activatedAt")
    created_at: str

    model_config = {"populate_by_name": True}


class ActivateWorkflowData(BaseModel):
    workflow_id: str = Field(..., alias="workflowId")
    status: str
    active_version: int = Field(..., alias="activeVersion")
    activated_at: str = Field(..., alias="activatedAt")
    executions_created: int = Field(..., alias="executionsCreated")
    runs_queued: int = Field(..., alias="runsQueued")
    message: str

    model_config = {"populate_by_name": True}


class UpdateWorkflowStatusRequest(BaseModel):
    status: Literal["active", "paused"]

    model_config = {"populate_by_name": True}


class RequeueWorkflowRunsData(BaseModel):
    workflow_id: str = Field(..., alias="workflowId")
    runs_enqueued: int = Field(..., alias="runsEnqueued")
    message: str

    model_config = {"populate_by_name": True}


class UpdateWorkflowStatusData(BaseModel):
    id: str
    name: str
    status: str
    active_version: int | None = Field(default=None, alias="activeVersion")
    activated_at: str | None = Field(default=None, alias="activatedAt")
    created_at: str = Field(..., alias="createdAt")
    runs_enqueued: int = Field(default=0, alias="runsEnqueued")

    model_config = {"populate_by_name": True}


class RecipientItemData(BaseModel):
    email: str


class RecipientCountsData(BaseModel):
    valid_count: int = Field(..., alias="validCount")
    invalid_count: int = Field(default=0, alias="invalidCount")

    model_config = {"populate_by_name": True}


class RecipientListData(BaseModel):
    recipients: list[RecipientItemData] = Field(default_factory=list)
    valid_count: int = Field(..., alias="validCount")
    invalid_count: int = Field(default=0, alias="invalidCount")

    model_config = {"populate_by_name": True}


class AddRecipientsRequest(BaseModel):
    emails: list[str] = Field(..., min_length=1)

    model_config = {"populate_by_name": True}


class RecipientUploadData(BaseModel):
    valid_count: int = Field(..., alias="validCount")
    invalid_count: int = Field(..., alias="invalidCount")
    valid_emails: list[str] = Field(default_factory=list, alias="validEmails")
    invalid_rows: list[dict[str, str]] = Field(default_factory=list, alias="invalidRows")
    recipients: list[RecipientItemData] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ReviewRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1)


class ReviewData(BaseModel):
    workflow_summary: dict[str, Any] = Field(alias="workflowSummary")
    email_summary: dict[str, Any] = Field(alias="emailSummary")
    recipient_count: int = Field(alias="recipientCount")
    schedule_summary: dict[str, Any] = Field(alias="scheduleSummary")
    review_status: str = Field(default="pending", alias="reviewStatus")
    activation_allowed: bool = Field(default=False, alias="activationAllowed")

    model_config = {"populate_by_name": True}


class SendEmailRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1, alias="workflowId")

    model_config = {"populate_by_name": True}


class EmailSendStatusData(BaseModel):
    status: str
    message_id: str | None = None
    message_ids: list[str] = Field(default_factory=list, alias="messageIds")
    recipient_count: int = Field(..., alias="recipientCount")
    step_id: str | None = Field(default=None, alias="stepId")

    model_config = {"populate_by_name": True}


class WebhookProcessData(BaseModel):
    status: str
    event_type: str | None = None
    duplicate: bool = False
    workflow_updated: bool = Field(default=False, alias="workflowUpdated")

    model_config = {"populate_by_name": True}


class AnalyticsData(BaseModel):
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    replied: int = 0
    failed: int = 0
    bounced: int = 0
