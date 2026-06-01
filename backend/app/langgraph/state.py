from typing import TypedDict


class MessageDict(TypedDict):
    role: str
    content: str


class CampaignState(TypedDict, total=False):
    workflow_id: str
    user_id: str
    messages: list[MessageDict]
    campaign_name: str | None
    business_goal: str | None
    product_info: str | None
    audience: str | None
    tone: str | None
    cta: str | None
    attachments: str | None
    landing_page: str | None
    product_image: str | None
    follow_up_strategy: str | None
    reply_strategy: str | None
    missing_fields: list[str]
    skipped_fields: list[str]
    brief_status: str | None
    brief_approved: bool
    campaign_brief: dict[str, object] | None
    workflow: dict[str, object] | None
    assistant_reply: str


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
    }
