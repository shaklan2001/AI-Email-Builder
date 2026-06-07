"""Tests for skip detection, defaults, and minimal product inference."""

from app.schemas.campaign import CampaignData
from app.services.campaign_field_policy import (
    CTA_URL_FIELD,
    EMAIL_LENGTH_FIELD,
    WANTS_CTA_FIELD,
    apply_field_defaults,
    condense_product_info,
    infer_cta_label_from_message,
    infer_product_from_minimal_message,
    is_declining_tweaks_message,
    is_no_cta_message,
    is_proceed_message,
    is_vague_product_info,
    parse_cta_label,
    parse_wants_cta,
    user_wants_cta_url,
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
    assert infer_product_from_minimal_message("my new product") is None


def test_is_vague_product_info() -> None:
    assert is_vague_product_info("new product")
    assert is_vague_product_info("my product")
    assert is_vague_product_info("a service")
    assert not is_vague_product_info("Half Moon Backpack")


def test_user_wants_cta_url_when_cta_is_set() -> None:
    campaign = CampaignData(product_info="CRM", cta="Book a Demo")
    assert user_wants_cta_url(campaign, [], wants_cta=True) is True

    default_campaign = CampaignData(product_info="CRM", cta="Learn More")
    assert user_wants_cta_url(default_campaign, [], wants_cta=True) is True

    assert user_wants_cta_url(CampaignData(product_info="CRM"), [], wants_cta=True) is False
    assert user_wants_cta_url(default_campaign, [], wants_cta=False) is False

    assert user_wants_cta_url(
        CampaignData(product_info="CRM"),
        [{"role": "user", "content": "use this cta link https://example.com/demo"}],
        wants_cta=True,
    ) is True


def test_resolve_skip_for_cta_without_button() -> None:
    skipped, patches = resolve_skip_for_field("cta", set(), latest_message="no")
    assert skipped == {"cta"}
    assert patches == {}

    skipped, patches = resolve_skip_for_field(
        "cta",
        set(),
        latest_message="you decide",
    )
    assert patches == {"cta": "Learn More"}


def test_is_no_cta_message() -> None:
    assert is_no_cta_message("no")
    assert is_no_cta_message("no button please")
    assert not is_no_cta_message("Learn More")


def test_proceed_phrases_include_casual_approval() -> None:
    assert is_proceed_message("everything look cool")
    assert not is_proceed_message("no")
    assert is_declining_tweaks_message("no")


def test_parse_wants_cta_and_labels() -> None:
    assert parse_wants_cta("yes") is True
    assert parse_wants_cta("Yeah!") is True
    assert parse_wants_cta("no") is False
    assert parse_wants_cta("link to my company website") is True
    assert parse_wants_cta(
        "yes i want a cta that books the call",
    ) is True
    assert parse_wants_cta(
        "no",
        campaign=CampaignData(product_info="CRM", cta="Learn More"),
    ) is True

    assert parse_cta_label("yes") is None
    assert parse_cta_label("Learn More") == "Learn More"
    assert parse_cta_label("Book a Demo") == "Book a Demo"
    assert infer_cta_label_from_message(
        "yes i want a cta that books the call",
    ) == "Book a Call"
    assert infer_cta_label_from_message("book a call") == "Book a Call"


def test_next_field_collects_cta_in_three_steps() -> None:
    prefs = {
        "follow_up_delay": _SAMPLE_DELAY,
        "email_length": _SAMPLE_PREFS["email_length"],
        "wants_follow_up": _SAMPLE_PREFS["wants_follow_up"],
    }
    ready = CampaignData(
        product_info="CRM",
        campaign_name="Outreach",
        audience="Founders",
    )
    assert (
        next_field_to_collect(ready, set(), **prefs)
        == WANTS_CTA_FIELD
    )

    wants_only = {**prefs, "wants_cta": True}
    assert (
        next_field_to_collect(ready, set(), **wants_only)
        == "cta"
    )

    labeled = CampaignData(
        product_info="CRM",
        campaign_name="Outreach",
        audience="Founders",
        cta="Book a Demo",
    )
    assert (
        next_field_to_collect(labeled, set(), **{**prefs, "wants_cta": True})
        == CTA_URL_FIELD
    )

    no_cta = CampaignData(
        product_info="CRM",
        campaign_name="Outreach",
        audience="Founders",
    )
    assert (
        next_field_to_collect(
            no_cta,
            set(),
            **{**prefs, "wants_cta": False},
        )
        is None
    )


def test_condense_product_info_from_business_description() -> None:
    raw = (
        "i run a freelance mobile development componet and i want to send email "
        "to the founders that are looking to build aap"
    )
    assert condense_product_info(raw) == "Freelance Mobile Development"

    assert condense_product_info("cursor ai") == "cursor ai"
    assert condense_product_info("my new product") is None


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
    assert resolved.cta is None
    assert resolved.audience == "General Customers"

    with_cta = apply_field_defaults(campaign, wants_cta=True)
    assert with_cta.cta == "Learn More"

    no_cta = apply_field_defaults(
        CampaignData(product_info="Tea", cta="Learn More"),
        wants_cta=False,
    )
    assert no_cta.cta is None


def test_collection_reply_asks_next_brief_field_when_prefs_collected() -> None:
    campaign = CampaignData(product_info="Chocolate")
    reply = build_collection_reply(
        campaign,
        follow_up_delay=_SAMPLE_DELAY,
        email_length=_SAMPLE_PREFS["email_length"],
        wants_follow_up=_SAMPLE_PREFS["wants_follow_up"],
    )
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
        == WANTS_CTA_FIELD
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
        WANTS_CTA_FIELD,
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
