"""Tests for email length and follow-up opt-in collection."""

from app.services.campaign_field_policy import (
    EMAIL_LENGTH_FIELD,
    FOLLOW_UP_DELAY_FIELD,
    WANTS_FOLLOW_UP_FIELD,
    is_ready_for_campaign_brief,
    next_field_to_collect,
)
from app.services.collection_preferences import (
    EMAIL_LENGTH_QUESTION,
    WANTS_FOLLOW_UP_QUESTION,
    format_email_length_brief,
    parse_email_length,
    parse_email_length_detail,
    parse_wants_follow_up,
)
from app.schemas.campaign import CampaignData
from app.services.conversation_response import _follow_up_question, build_collection_reply


def test_next_field_after_product_is_email_length() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    assert next_field_to_collect(campaign, set()) == EMAIL_LENGTH_FIELD


def test_next_field_after_email_length_is_follow_up_preference() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    assert (
        next_field_to_collect(campaign, set(), email_length="medium")
        == WANTS_FOLLOW_UP_FIELD
    )


def test_next_field_after_no_follow_up_skips_delay() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    assert (
        next_field_to_collect(
            campaign,
            set(),
            email_length="short",
            wants_follow_up=False,
        )
        == "campaign_name"
    )


def test_next_field_after_yes_follow_up_asks_delay() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    assert (
        next_field_to_collect(
            campaign,
            set(),
            email_length="medium",
            wants_follow_up=True,
            follow_up_delay=None,
        )
        == FOLLOW_UP_DELAY_FIELD
    )


def test_is_ready_for_brief_without_follow_up() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    assert is_ready_for_campaign_brief(
        campaign,
        email_length="medium",
        wants_follow_up=False,
        follow_up_delay=None,
    )


def test_is_ready_for_brief_with_follow_up_requires_delay() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    assert not is_ready_for_campaign_brief(
        campaign,
        email_length="medium",
        wants_follow_up=True,
        follow_up_delay=None,
    )
    assert is_ready_for_campaign_brief(
        campaign,
        email_length="medium",
        wants_follow_up=True,
        follow_up_delay={"value": 1, "unit": "hours"},
    )


def test_parse_email_length_and_follow_up_preference() -> None:
    assert parse_email_length("short please") == "short"
    assert parse_email_length("keep it medium") == "medium"
    assert parse_wants_follow_up("yes") is True
    assert parse_wants_follow_up("no follow up needed") is False


def test_parse_bare_number_as_word_count() -> None:
    parsed = parse_email_length_detail("160")
    assert parsed is not None
    assert parsed.words == 160
    assert parsed.category == "long"
    assert parse_email_length("160") == "long"


def test_parse_number_with_words_suffix() -> None:
    parsed = parse_email_length_detail("160 words")
    assert parsed is not None
    assert parsed.words == 160
    assert parsed.category == "long"


def test_format_email_length_brief_shows_word_count() -> None:
    assert format_email_length_brief("long", words=160) == "160 words (Long)"


def test_collection_questions() -> None:
    assert EMAIL_LENGTH_QUESTION in _follow_up_question(EMAIL_LENGTH_FIELD)
    assert WANTS_FOLLOW_UP_QUESTION in _follow_up_question(WANTS_FOLLOW_UP_FIELD)


def test_collection_reply_asks_email_length_before_follow_up() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    reply = build_collection_reply(campaign)
    assert "How long should the initial outreach email be?" in reply
    assert "should I send a follow-up email" not in reply
