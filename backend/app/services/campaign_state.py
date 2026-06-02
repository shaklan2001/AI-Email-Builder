"""Single source of truth helpers for campaign state and generation."""

from __future__ import annotations

from app.langgraph.state import CampaignState, campaign_data_from_state
from app.schemas.campaign import CampaignData
from app.schemas.campaign_brief import CampaignBriefData
from app.services.campaign_field_policy import (
    apply_field_defaults,
    normalize_skipped_fields,
)


def campaign_from_brief_dict(
    brief: dict[str, object],
    *,
    fallback: CampaignData | None = None,
) -> CampaignData:
    """Build CampaignData from the approved campaign brief (authoritative for generation)."""
    base = fallback or CampaignData()
    try:
        parsed = CampaignBriefData.model_validate(
            {
                "campaignName": brief.get("campaignName"),
                "businessGoal": brief.get("businessGoal"),
                "audience": brief.get("audience"),
                "productInfo": brief.get("productInfo"),
                "tone": brief.get("tone"),
                "cta": brief.get("cta"),
                "landingPage": brief.get("landingPage"),
                "attachments": brief.get("attachments"),
            },
        )
    except Exception:
        return base

    image_url: str | None = base.product_image
    attachments = parsed.attachments
    if attachments and str(attachments).strip().lower().startswith("product image:"):
        image_url = str(attachments).replace("Product image:", "", 1).strip()

    return CampaignData(
        campaign_name=parsed.campaign_name or base.campaign_name,
        business_goal=parsed.business_goal or base.business_goal,
        product_info=parsed.product_info or base.product_info,
        audience=parsed.audience or base.audience,
        tone=parsed.tone or base.tone,
        cta=parsed.cta or base.cta,
        landing_page=parsed.landing_page or base.landing_page,
        product_image=image_url,
    )


def campaign_for_generation(state: CampaignState) -> CampaignData:
    """
    Campaign used for workflow and email generation.
    Prefer the approved brief; fall back to LangGraph state fields.
    """
    skipped = normalize_skipped_fields(state.get("skipped_fields"))
    base = apply_field_defaults(campaign_data_from_state(state), skipped)
    brief = state.get("campaign_brief")
    if isinstance(brief, dict) and brief:
        return apply_field_defaults(campaign_from_brief_dict(brief, fallback=base), skipped)
    return base
