"""Rule-based campaign field extraction from chat messages."""

from app.schemas.campaign import CampaignData
from app.services.campaign_extraction import extract_from_latest_user_message
from app.services.campaign_revision import (
    is_explicit_field_update,
    is_revision_message,
    should_overwrite_campaign_fields,
)


def test_product_name_is_overwrites_existing_product() -> None:
    before = CampaignData(product_info="Old Product", campaign_name="Old Campaign")
    messages = [{"role": "user", "content": "the product name is cursor ai"}]

    updated = extract_from_latest_user_message(messages, before)

    assert updated.product_info == "cursor ai"
    assert updated.campaign_name == "Old Campaign"


def test_campaign_name_is_does_not_touch_product() -> None:
    before = CampaignData(product_info="Widgets", campaign_name="Old Name")
    messages = [{"role": "user", "content": "the campaign name is cursor ai"}]

    updated = extract_from_latest_user_message(messages, before)

    assert updated.campaign_name == "cursor ai"
    assert updated.product_info == "Widgets"


def test_explicit_field_update_detected() -> None:
    assert is_explicit_field_update("the product name is cursor ai")
    assert is_revision_message("the product name is cursor ai")
    assert should_overwrite_campaign_fields("the product name is cursor ai")


def test_editing_brief_status_enables_overwrite_mode() -> None:
    assert should_overwrite_campaign_fields(
        "cursor ai",
        brief_status="editing",
    )
    assert not should_overwrite_campaign_fields(
        "cursor ai",
        brief_status="pending_approval",
    )


def test_remove_landing_page_clears_field() -> None:
    before = CampaignData(
        product_info="CRM",
        landing_page="https://example.com",
    )
    messages = [{"role": "user", "content": "remove the landing page"}]

    updated = extract_from_latest_user_message(messages, before)

    assert updated.landing_page is None
    assert updated.product_info == "CRM"


def test_change_product_with_revision_phrase() -> None:
    before = CampaignData(product_info="AirPure")
    messages = [{"role": "user", "content": "change product to Cursor AI"}]

    updated = extract_from_latest_user_message(messages, before, revision=True)

    assert updated.product_info == "Cursor AI"
