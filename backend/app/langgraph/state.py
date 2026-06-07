from typing import TypedDict


class MessageDict(TypedDict):
    role: str
    content: str


class ConversationState(TypedDict, total=False):
    """Single source of truth for a user chat thread (persisted in MongoDB)."""

    campaign_id: str
    workflow_id: str
    user_id: str
    thread_id: str
    messages: list[MessageDict]
    campaign_brief: dict[str, object] | None
    workflow: dict[str, object] | None
    email_templates: list[dict[str, object]]
    recipients: list[dict[str, object]]
    missing_fields: list[str]
    current_stage: str
    approval_status: str
    campaign_name: str | None
    business_goal: str | None
    product_info: str | None
    audience: str | None
    tone: str | None
    cta: str | None
    attachments: str | None
    competitors: str | None
    landing_page: str | None
    product_image: str | None
    follow_up_strategy: str | None
    follow_up_delay: dict[str, object] | None
    wants_follow_up: bool | None
    wants_cta: bool | None
    email_length: str | None
    email_length_words: int | None
    reply_strategy: str | None
    skipped_fields: list[str]
    brief_status: str | None
    brief_approved: bool
    review_status: str | None
    regenerate_workflow: bool
    leads: dict[str, object]
    conversation_threads: list[dict[str, object]]
    reply_intent: str | None
    tool_calls: list[dict[str, object]]
    lead_status: str | None
    generated_responses: list[dict[str, object]]
    assistant_reply: str


# LangGraph graph uses the same shape as persisted conversation state.
CampaignState = ConversationState


from app.schemas.campaign import CampaignData


def campaign_data_from_state(state: CampaignState) -> CampaignData:

    return CampaignData(
        campaign_name=state.get("campaign_name"),
        business_goal=state.get("business_goal"),
        product_info=state.get("product_info"),
        audience=state.get("audience"),
        tone=state.get("tone"),
        cta=state.get("cta"),
        landing_page=state.get("landing_page"),
        product_image=state.get("product_image"),
        attachments=state.get("attachments"),
        competitors=state.get("competitors"),
    )


def apply_campaign_data(state: CampaignState, data: CampaignData) -> dict[str, str | None]:
    return {
        "campaign_name": data.campaign_name,
        "business_goal": data.business_goal,
        "product_info": data.product_info,
        "audience": data.audience,
        "tone": data.tone,
        "cta": data.cta,
        "landing_page": data.landing_page,
        "product_image": data.product_image,
        "attachments": data.attachments,
        "competitors": data.competitors,
    }
