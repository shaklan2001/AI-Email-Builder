"""Tests for skip detection, defaults, and minimal product inference."""

from app.schemas.campaign import CampaignData
from app.services.campaign_field_policy import (
    EMAIL_LENGTH_FIELD,
    apply_field_defaults,
    infer_product_from_minimal_message,
    is_skip_message,
    missing_required_fields,
    next_field_to_collect,
    resolve_skip_for_field,
    mark_all_optional_skipped,
)
from app.services.campaign_field_policy import FOLLOW_UP_DELAY_FIELD
from app.services.conversation_response import (
    build_collection_reply,
    next_missing_field,
    progress_percent,
)

_SAMPLE_DELAY = {"value": 3, "unit": "days"}
_SAMPLE_PREFS = {
    "email_length": "medium",
    "wants_follow_up": True,
}


def test_is_skip_message_detects_phrases() -> None:
    assert is_skip_message("skip")
    assert is_skip_message("none")
    assert is_skip_message("nothing")
    assert is_skip_message("Not sure")
    assert is_skip_message("I don't know")
    assert is_skip_message("no preference")
    assert is_skip_message("doesn't matter")
    assert is_skip_message("recommend for me")
    assert is_skip_message("anything works")
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
    assert next_missing_field(filled) == EMAIL_LENGTH_FIELD
    assert (
        next_missing_field(
            filled,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        == "campaign_name"
    )
    assert progress_percent(filled) == 100


def test_skip_optional_applies_default_and_stops_asking() -> None:
    campaign = CampaignData(product_info="Chocolate")
    skipped: set[str] = set()

    assert (
        next_field_to_collect(campaign, skipped, include_optional=True)
        == EMAIL_LENGTH_FIELD
    )

    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        == "campaign_name"
    )

    skipped, _ = resolve_skip_for_field("campaign_name", skipped)
    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        == "audience"
    )


def test_apply_field_defaults() -> None:
    campaign = CampaignData(product_info="Tea")
    resolved = apply_field_defaults(campaign)
    assert resolved.business_goal == "Product Promotion"
    assert resolved.tone == "Professional"
    assert resolved.cta == "Learn More"
    assert resolved.audience == "General Customers"


def test_collection_reply_asks_next_brief_field_when_prefs_collected() -> None:
    campaign = CampaignData(product_info="Chocolate")
    reply = build_collection_reply(
        campaign,
        follow_up_delay=_SAMPLE_DELAY,
        email_length=_SAMPLE_PREFS["email_length"],
        wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
    )
    assert "✓ Product: Chocolate" in reply
    assert "name this campaign" in reply.lower()


def test_skip_does_not_repeat_same_optional_question() -> None:
    campaign = CampaignData(product_info="Tea")
    skipped: set[str] = set()
    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        == "campaign_name"
    )

    skipped, _ = resolve_skip_for_field("campaign_name", skipped)
    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        == "audience"
    )
    skipped, patches = resolve_skip_for_field("audience", skipped)
    campaign = campaign.apply_updates(patches)
    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        == "cta"
    )


def test_proceed_marks_all_optional_skipped() -> None:
    skipped = mark_all_optional_skipped(set())
    campaign = CampaignData(product_info="Coffee")
    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        is None
    )


def test_skip_competitors_and_attachments_without_defaults() -> None:
    campaign = CampaignData(product_info="SaaS tool")
    skipped: set[str] = set()
    for field in (
        "campaign_name",
        "business_goal",
        "tone",
        "audience",
        "cta",
        "landing_page",
        "product_image",
    ):
        skipped, patches = resolve_skip_for_field(field, skipped)
        campaign = campaign.apply_updates(patches)

    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        == "attachments"
    )
    skipped, patches = resolve_skip_for_field("attachments", skipped)
    assert patches == {}
    assert "attachments" in skipped

    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        == "competitors"
    )
    skipped, patches = resolve_skip_for_field("competitors", skipped)
    assert patches == {}
    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay=_SAMPLE_DELAY,
            email_length=_SAMPLE_PREFS["email_length"],
            wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
        )
        is None
    )
