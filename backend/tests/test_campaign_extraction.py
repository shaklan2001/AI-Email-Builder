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


def test_product_name_typo_anem_is_extracted() -> None:
    before = CampaignData(
        product_info="software that provide user the authentication for their website",
    )
    messages = [
        {
            "role": "user",
            "content": (
                "software that provide user the authentication for their website "
                "this is decription the product anem is Clerk"
            ),
        },
    ]
    updated = extract_from_latest_user_message(messages, before)
    assert updated.product_info == "Clerk"


def test_explicit_field_update_detected() -> None:
    assert is_explicit_field_update("the product name is cursor ai")
    assert is_revision_message("the product name is cursor ai")
    assert should_overwrite_campaign_fields("the product name is cursor ai")


def test_editing_brief_status_enables_overwrite_mode() -> None:
    assert should_overwrite_campaign_fields(
        "cursor ai",
        brief_status="editing",
    )


def test_pending_approval_allows_explicit_field_update() -> None:
    assert should_overwrite_campaign_fields(
        "the campaign name is IT Serviceee",
        brief_status="pending_approval",
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


def test_campagon_typo_extracts_campaign_name() -> None:
    before = CampaignData(product_info="IT service")
    messages = [
        {
            "role": "user",
            "content": "i want to make teh campagon name as teh IT Serviceee",
        },
    ]

    updated = extract_from_latest_user_message(messages, before)

    assert updated.campaign_name == "IT Serviceee"


def test_change_product_with_revision_phrase() -> None:
    before = CampaignData(product_info="AirPure")
    messages = [{"role": "user", "content": "change product to Cursor AI"}]

    updated = extract_from_latest_user_message(messages, before, revision=True)

    assert updated.product_info == "Cursor AI"


def test_image_url_does_not_set_landing_page() -> None:
    amazon = "https://www.amazon.in/Half-Moon-Waterproof-Backpack-Students/dp/B085MHDJ93"
    before = CampaignData(product_info="Backpack")
    messages = [
        {
            "role": "user",
            "content": f"add a image url that goes with the email {amazon}",
        },
    ]

    updated = extract_from_latest_user_message(messages, before, revision=True)

    assert updated.product_image == amazon
    assert updated.landing_page is None


def test_image_only_correction_clears_duplicate_landing_page() -> None:
    amazon = "https://www.amazon.in/Half-Moon-Waterproof-Backpack-Students/dp/B085MHDJ93"
    before = CampaignData(
        product_info="Backpack",
        landing_page=amazon,
        product_image=amazon,
    )
    messages = [
        {
            "role": "user",
            "content": f"i only want to set this as the images url {amazon}",
        },
    ]

    updated = extract_from_latest_user_message(messages, before, revision=True)

    assert updated.product_image == amazon
    assert updated.landing_page is None


def test_it_services_business_description_extracts_product() -> None:
    before = CampaignData()
    messages = [
        {"role": "user", "content": "i was makeing for it services"},
    ]
    updated = extract_from_latest_user_message(messages, before)
    assert updated.product_info == "IT Services"

    messages2 = [
        {
            "role": "user",
            "content": "my business is that i provide teh it service smake automation for the products",
        },
    ]
    updated2 = extract_from_latest_user_message(messages2, before)
    assert updated2.product_info == "IT Services & Automation"


def test_vague_new_product_is_not_extracted() -> None:
    before = CampaignData()
    messages = [
        {"role": "user", "content": "i want to send a email for my new product"},
    ]

    updated = extract_from_latest_user_message(messages, before)

    assert updated.product_info is None


def test_business_pitch_condenses_product_and_extracts_audience() -> None:
    before = CampaignData()
    message = (
        "so basically my product is i run a freelance mobile development componet "
        "and i want to send email to the founders that are looking to build aap"
    )
    messages = [{"role": "user", "content": message}]

    updated = extract_from_latest_user_message(messages, before)

    assert updated.product_info == "Freelance Mobile Development"
    assert updated.audience == "founders that are looking to build aap"
