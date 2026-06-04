"""Tests for skip detection, defaults, and minimal product inference."""

from app.schemas.campaign import CampaignData
from app.services.campaign_field_policy import (
    apply_field_defaults,
    infer_product_from_minimal_message,
    is_skip_message,
    missing_required_fields,
    next_field_to_collect,
    resolve_skip_for_field,
)
from app.services.conversation_response import (
    build_collection_reply,
    next_missing_field,
    progress_percent,
)


def test_is_skip_message_detects_phrases() -> None:
    assert is_skip_message("skip")
    assert is_skip_message("Not sure")
    assert is_skip_message("I don't know")
    assert is_skip_message("no preference")
    assert not is_skip_message("professional tone")


def test_infer_product_from_minimal_message() -> None:
    assert infer_product_from_minimal_message("Chocolate business") == "Chocolate"
    assert infer_product_from_minimal_message("selling organic tea") == "Organic Tea"


def test_only_product_is_required() -> None:
    campaign = CampaignData()
    assert missing_required_fields(campaign) == ["product_info"]
    assert next_missing_field(campaign) == "product_info"

    filled = CampaignData(product_info="Chocolate")
    assert missing_required_fields(filled) == []
    assert next_missing_field(filled) is None
    assert progress_percent(filled) == 100


def test_skip_optional_applies_default_and_stops_asking() -> None:
    campaign = CampaignData(product_info="Chocolate")
    skipped: set[str] = set()

    assert next_field_to_collect(campaign, skipped, include_optional=True) == "business_goal"

    skipped, patches = resolve_skip_for_field("business_goal", skipped)
    campaign = campaign.apply_updates(patches)

    assert "business_goal" in skipped
    assert campaign.business_goal == "Product Promotion"
    assert next_field_to_collect(campaign, skipped, include_optional=True) == "audience"


def test_apply_field_defaults() -> None:
    campaign = CampaignData(product_info="Tea")
    resolved = apply_field_defaults(campaign)
    assert resolved.business_goal == "Product Promotion"
    assert resolved.tone == "Professional"
    assert resolved.cta == "Learn More"
    assert resolved.audience == "General Customers"


def test_collection_reply_shows_assumptions_when_product_known() -> None:
    campaign = CampaignData(product_info="Chocolate")
    reply = build_collection_reply(campaign)
    assert "Chocolate" in reply
    assert "Assumptions:" in reply
    assert "customize" in reply.lower()
    assert "business goal" not in reply.lower() or "assumptions" in reply.lower()
