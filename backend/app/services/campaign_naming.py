"""Auto-generate dashboard campaign titles from collected campaign context."""

from __future__ import annotations

import re

from app.providers.llm.base import LLMProvider, LLMProviderError
from app.schemas.campaign import CampaignData
from app.services.campaign_field_policy import is_vague_product_info

_PLACEHOLDER_NAMES = frozenset(
    {
        "",
        "untitled campaign",
        "untitled",
        "new campaign",
        "campaign",
        "draft campaign",
    },
)

_NAME_SYSTEM = """You name email outreach campaigns for a dashboard list.
Given product/service, goal, and audience, return ONE short title (2–6 words).
Use title case. No quotes, no explanation, no punctuation at the end.
Examples: "Sinch Converse Launch", "IT Services Outreach", "Half Moon Backpack Promo"."""


def is_placeholder_campaign_name(name: str | None) -> bool:
    if name is None:
        return True
    stripped = str(name).strip()
    if not stripped:
        return True
    return stripped.lower() in _PLACEHOLDER_NAMES


def suggest_campaign_name_rule(campaign: CampaignData) -> str | None:
    """Deterministic fallback when the LLM is unavailable."""
    product = (campaign.product_info or "").strip()
    if not product or is_vague_product_info(product):
        return None

    goal = (campaign.business_goal or "").strip().lower()
    if not goal or goal == "product promotion":
        suffix = "Outreach"
    elif "demo" in goal:
        suffix = "Demo Drive"
    elif "visit" in goal or "traffic" in goal:
        suffix = "Traffic Campaign"
    else:
        words = re.sub(r"[^\w\s]", "", campaign.business_goal or "").split()
        suffix = " ".join(words[:2]).title() if words else "Outreach"

    name = f"{product} {suffix}".strip()
    return name[:80] if name else None


def _normalize_generated_name(raw: str) -> str | None:
    cleaned = raw.strip().strip("\"'").rstrip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned or is_placeholder_campaign_name(cleaned):
        return None
    if len(cleaned) > 80:
        cleaned = cleaned[:80].rsplit(" ", 1)[0]
    return cleaned or None


async def generate_campaign_name(
    llm: LLMProvider,
    campaign: CampaignData,
) -> str | None:
    """LLM-suggested title with rule-based fallback."""
    fallback = suggest_campaign_name_rule(campaign)
    if fallback is None:
        return None

    audience = (campaign.audience or "General customers").strip()
    goal = (campaign.business_goal or "Product promotion").strip()
    product = campaign.product_info or ""

    user_prompt = (
        f"Product / service: {product}\n"
        f"Business goal: {goal}\n"
        f"Target audience: {audience}\n\n"
        "Campaign title:"
    )
    try:
        raw = await llm.generate(_NAME_SYSTEM, user_prompt)
    except LLMProviderError:
        return fallback

    parsed = _normalize_generated_name(raw)
    return parsed or fallback


async def resolve_campaign_display_name(
    *,
    llm: LLMProvider,
    campaign: CampaignData,
    state_name: str | None,
    record_name: str | None = None,
) -> str | None:
    """Pick or generate a name when the workflow still uses a placeholder title."""
    for candidate in (state_name, record_name):
        if candidate and not is_placeholder_campaign_name(candidate):
            return str(candidate).strip()

    if not campaign.product_info or is_vague_product_info(campaign.product_info):
        return None

    return await generate_campaign_name(llm, campaign)
