"""Auto-generated campaign dashboard titles."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.campaign import CampaignData
from app.services.campaign_naming import (
    generate_campaign_name,
    is_placeholder_campaign_name,
    resolve_campaign_display_name,
    suggest_campaign_name_rule,
)


def test_placeholder_detection() -> None:
    assert is_placeholder_campaign_name("Untitled Campaign")
    assert is_placeholder_campaign_name(None)
    assert not is_placeholder_campaign_name("Sinch Converse Launch")


def test_suggest_campaign_name_rule_from_product() -> None:
    campaign = CampaignData(
        product_info="Sinch Converse",
        business_goal="Product Promotion",
        audience="Enterprise IT",
    )
    assert suggest_campaign_name_rule(campaign) == "Sinch Converse Outreach"


@pytest.mark.asyncio
async def test_generate_campaign_name_falls_back_when_llm_fails() -> None:
    llm = MagicMock()
    llm.generate = AsyncMock(side_effect=Exception("offline"))
    from app.providers.llm.base import LLMProviderError

    llm.generate = AsyncMock(side_effect=LLMProviderError("offline"))
    campaign = CampaignData(product_info="Half Moon Backpack")
    name = await generate_campaign_name(llm, campaign)
    assert name == "Half Moon Backpack Outreach"


@pytest.mark.asyncio
async def test_resolve_skips_when_user_named_campaign() -> None:
    llm = MagicMock()
    campaign = CampaignData(product_info="CRM", campaign_name="Q4 CRM Push")
    resolved = await resolve_campaign_display_name(
        llm=llm,
        campaign=campaign,
        state_name="Q4 CRM Push",
    )
    assert resolved == "Q4 CRM Push"
    llm.generate.assert_not_called()
