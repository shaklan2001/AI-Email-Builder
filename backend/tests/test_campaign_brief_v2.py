"""Campaign brief v2 fields (spec 28)."""

from app.schemas.campaign import CampaignData
from app.schemas.campaign_brief import DEFAULT_REPLY_HANDLING, DEFAULT_TOOLS_AVAILABLE
from app.schemas.follow_up_delay import FollowUpDelay
from app.services.conversation_response import build_campaign_brief, format_campaign_brief_text
from app.services.follow_up_delay import format_follow_up_delay_brief


def test_format_follow_up_delay_brief() -> None:
    assert format_follow_up_delay_brief(FollowUpDelay(value=3, unit="days")) == "3 Days"
    assert format_follow_up_delay_brief(FollowUpDelay(value=1, unit="days")) == "1 Day"


def test_build_campaign_brief_v2_fields() -> None:
    campaign = CampaignData(
        product_info="AI Sales Automation",
        audience="SaaS Founders",
        tone="Professional",
        cta="Book Demo",
        landing_page="https://example.com",
        product_image="https://example.com/image.png",
    )
    delay = {"value": 3, "unit": "days"}
    brief = build_campaign_brief(
        campaign,
        campaign_name="ZyLabs Outreach",
        messages=[],
        product_image="https://example.com/image.png",
        landing_page="https://example.com",
        follow_up_delay=delay,
        wants_follow_up=True,
        email_length="medium",
        state_only=True,
    )

    assert brief.campaign_name == "ZyLabs Outreach"
    assert brief.product_info == "AI Sales Automation"
    assert brief.audience == "SaaS Founders"
    assert brief.cta == "Book Demo"
    assert brief.follow_up_delay == "3 Days"
    assert brief.reply_handling == DEFAULT_REPLY_HANDLING
    assert brief.tools_available == list(DEFAULT_TOOLS_AVAILABLE)

    api = brief.to_api_dict()
    assert api["emailLength"] == "Medium"
    assert api["followUpEnabled"] == "Yes — send follow-up if no reply"
    assert api["followUpDelay"] == "3 Days"
    assert api["replyHandling"] == DEFAULT_REPLY_HANDLING
    assert api["toolsAvailable"] == list(DEFAULT_TOOLS_AVAILABLE)


def test_brief_from_state_includes_email_length_and_follow_up() -> None:
    from app.services.workflow_state_response import brief_from_state

    state = {
        "brief_status": "pending_approval",
        "current_stage": "campaign_brief",
        "campaign_brief": {
            "campaignName": None,
            "productInfo": "Backpack",
            "audience": "General Customers",
            "cta": "Learn More",
            "tone": "Professional",
            "landingPage": None,
            "imageUrl": "https://example.com/image.png",
            "emailLength": "Medium",
            "followUpEnabled": "No — initial email only",
            "followUpDelay": "None — initial email only",
            "replyHandling": DEFAULT_REPLY_HANDLING,
            "toolsAvailable": list(DEFAULT_TOOLS_AVAILABLE),
        },
    }
    brief = brief_from_state(state)
    assert brief is not None
    assert brief.email_length == "Medium"
    assert brief.follow_up_enabled == "No — initial email only"

    text = format_campaign_brief_text(brief)
    assert "Product:" in text
    assert "Follow-Up Delay:" in text
    assert "Reply Handling:" in text
    assert "✓ Company Information" in text
    assert "✓ Demo Booking" in text
