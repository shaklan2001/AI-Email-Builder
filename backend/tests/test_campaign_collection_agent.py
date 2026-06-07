"""Campaign collection agent — skip/delegate, missing_fields, no repeat questions."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.campaign_collection_agent import CampaignCollectionAgent
from app.repositories.workflow_repository import workflow_repository
from app.langgraph.state import ConversationState
from app.schemas.campaign import CampaignData
from app.services.campaign_field_policy import (
    EMAIL_LENGTH_FIELD,
    FOLLOW_UP_DELAY_FIELD,
    REQUIRED_FIELD,
    WANTS_CTA_FIELD,
    WANTS_FOLLOW_UP_FIELD,
    is_proceed_message,
    is_skip_message,
    next_field_to_collect,
    resolve_skip_for_field,
)
from app.services.conversation_response import build_collection_reply


def test_delegate_phrases_treated_as_skip() -> None:
    assert is_skip_message("recommend for me")
    assert is_skip_message("anything works")
    assert is_skip_message("you decide")
    assert is_skip_message("pick for me")
    assert is_skip_message("you can decide your self")


@pytest.mark.asyncio
async def test_delegate_email_length_advances_state() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(
        return_value=CampaignData(product_info="CRM PRODUCT"),
    )
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [{"role": "user", "content": "you can decide your self"}],
        "product_info": "CRM PRODUCT",
        "skipped_fields": [],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("email_length") == "medium"
    assert EMAIL_LENGTH_FIELD in updates.get("skipped_fields", [])


@pytest.mark.asyncio
async def test_acknowledgement_defaults_next_preference_field() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(return_value=CampaignData(product_info="CRM"))
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [{"role": "user", "content": "oky"}],
        "product_info": "CRM",
        "email_length": "medium",
        "skipped_fields": [EMAIL_LENGTH_FIELD],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("wants_follow_up") is True
    assert WANTS_FOLLOW_UP_FIELD in updates.get("skipped_fields", [])


@pytest.mark.asyncio
async def test_skip_email_length_applies_default_and_advances() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(
        return_value=CampaignData(product_info="SaaS CRM"),
    )
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [{"role": "user", "content": "recommend for me"}],
        "product_info": "SaaS CRM",
        "skipped_fields": [],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("email_length") == "medium"
    assert EMAIL_LENGTH_FIELD in updates.get("skipped_fields", [])
    merged: ConversationState = {**state, **updates}  # type: ignore[misc]
    assert EMAIL_LENGTH_FIELD not in agent.missing_fields_snapshot(merged)["missing_fields"]


def test_skip_optional_does_not_repeat_question() -> None:
    campaign = CampaignData(product_info="Tea")
    skipped: set[str] = set()
    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay={"value": 3, "unit": "days"},
            email_length="medium",
            wants_follow_up=True,
        )
        == "campaign_name"
    )
    skipped, patches = resolve_skip_for_field("campaign_name", skipped)
    assert "campaign_name" in skipped
    assert patches == {}
    assert (
        next_field_to_collect(
            campaign,
            skipped,
            include_optional=True,
            follow_up_delay={"value": 3, "unit": "days"},
            email_length="medium",
            wants_follow_up=True,
        )
        != "campaign_name"
    )


def test_collection_reply_mentions_delegate_options() -> None:
    campaign = CampaignData(product_info="Widgets")
    reply = build_collection_reply(
        campaign,
        follow_up_delay=None,
    )
    assert "email" in reply.lower()


@pytest.mark.asyncio
async def test_affirmation_accepts_inferred_follow_up_delay() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(
        return_value=CampaignData(product_info="IT service"),
    )
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [
            {"role": "assistant", "content": "When should I send the follow-up? 5 days?"},
            {"role": "user", "content": "yes"},
        ],
        "product_info": "IT service",
        "email_length": "medium",
        "wants_follow_up": True,
        "skipped_fields": [],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("follow_up_delay") == {"value": 5, "unit": "days"}
    assert FOLLOW_UP_DELAY_FIELD in updates.get("skipped_fields", [])


@pytest.mark.asyncio
async def test_email_length_update_during_pending_approval() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(
        return_value=CampaignData(product_info="CRM", tone="Friendly"),
    )
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [{"role": "user", "content": "keep it 80 words"}],
        "product_info": "CRM",
        "email_length": "medium",
        "email_length_words": None,
        "wants_follow_up": True,
        "follow_up_delay": {"value": 6, "unit": "hours"},
        "brief_status": "pending_approval",
        "skipped_fields": [EMAIL_LENGTH_FIELD, WANTS_FOLLOW_UP_FIELD, FOLLOW_UP_DELAY_FIELD],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("email_length") == "short"
    assert updates.get("email_length_words") == 80


@pytest.mark.asyncio
async def test_looks_good_approval_preserves_brief_and_product() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(return_value=CampaignData())
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [{"role": "user", "content": "noy it look good"}],
        "product_info": "new product",
        "brief_approved": True,
        "brief_status": "approved",
        "email_length": "medium",
        "wants_follow_up": False,
        "campaign_brief": {
            "productInfo": "IT Services",
            "audience": "General Customers",
            "emailLength": "Medium",
            "followUpEnabled": "No — initial email only",
        },
        "skipped_fields": [],
    }
    updates = await agent.extract_and_update(state)
    assert "brief_approved" not in updates or updates.get("brief_approved") is not False
    assert "campaign_brief" not in updates
    assert updates.get("product_info") == "IT Services"
    merged: ConversationState = {**state, **updates}  # type: ignore[misc]
    assert merged.get("wants_follow_up") is False


@pytest.mark.asyncio
async def test_follow_up_request_during_pending_approval_updates_state() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(return_value=CampaignData(product_info="Sinch"))
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [
            {
                "role": "user",
                "content": "i want a follow email after 5 days if user do not reply",
            },
        ],
        "product_info": "Sinch",
        "email_length": "medium",
        "wants_follow_up": False,
        "brief_status": "pending_approval",
        "skipped_fields": [EMAIL_LENGTH_FIELD, WANTS_FOLLOW_UP_FIELD],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("wants_follow_up") is True
    assert updates.get("follow_up_delay") == {"value": 5, "unit": "days"}


@pytest.mark.asyncio
async def test_approval_syncs_follow_up_from_brief() -> None:
    llm = MagicMock()
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [{"role": "user", "content": "looks good"}],
        "product_info": "Sinch",
        "wants_follow_up": False,
        "brief_status": "approved",
        "brief_approved": True,
        "campaign_brief": {
            "productInfo": "Sinch",
            "followUpEnabled": "Yes — send follow-up if no reply",
            "followUpDelay": "5 Days",
        },
        "skipped_fields": [],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("wants_follow_up") is True
    assert updates.get("follow_up_delay") == {"value": 5, "unit": "days"}


@pytest.mark.asyncio
async def test_it_services_message_sets_product() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(return_value=CampaignData())
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [
            {"role": "user", "content": "i was makeing for it services"},
        ],
        "skipped_fields": [],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("product_info") == "IT Services"


@pytest.mark.asyncio
async def test_medium_answer_sets_email_length() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(return_value=CampaignData())
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [
            {"role": "assistant", "content": "Short, medium, or long?"},
            {"role": "user", "content": "medium"},
        ],
        "product_info": "Half Moon Backpack",
        "skipped_fields": [],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("email_length") == "medium"


@pytest.mark.asyncio
async def test_vague_product_is_not_accepted() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(
        return_value=CampaignData(product_info="new product"),
    )
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [
            {
                "role": "user",
                "content": "i want to send a email for my new product",
            },
        ],
        "skipped_fields": [],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("product_info") is None
    assert "product_info" in updates.get("missing_fields", [])


@pytest.mark.asyncio
async def test_auto_names_campaign_when_product_known() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(
        return_value=CampaignData(product_info="Sinch Converse"),
    )
    llm.generate = AsyncMock(return_value="Sinch Converse Launch")
    agent = CampaignCollectionAgent(llm=llm)
    workflow_repository.get_by_id = AsyncMock(return_value=None)
    workflow_repository.update_name = AsyncMock()
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [
            {"role": "user", "content": "email campaign for Sinch Converse enterprise IT"},
        ],
        "campaign_name": None,
        "skipped_fields": [],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("campaign_name") == "Sinch Converse Launch"
    assert "campaign_name" in updates.get("skipped_fields", [])


@pytest.mark.asyncio
async def test_extract_populates_missing_fields() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(return_value=CampaignData())
    agent = CampaignCollectionAgent(llm=llm)
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [{"role": "user", "content": "hello"}],
    }
    updates = await agent.extract_and_update(state)
    missing = updates.get("missing_fields")
    assert isinstance(missing, list)
    assert "product_info" in missing or REQUIRED_FIELD in missing


def test_proceed_phrases_include_lock_it() -> None:
    assert is_proceed_message("no that fine lock it")
    assert is_proceed_message("lock it")


@pytest.mark.asyncio
async def test_no_after_cta_details_does_not_clear_cta() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(
        return_value=CampaignData(
            product_info="Web Dev",
            cta="Learn More",
            landing_page="https://www.example.com/",
        ),
    )
    llm.generate = AsyncMock(return_value="Web Dev Outreach")
    agent = CampaignCollectionAgent(llm=llm)
    workflow_repository.get_by_id = AsyncMock(return_value=None)
    workflow_repository.update_name = AsyncMock()
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [
            {"role": "assistant", "content": "Want to tweak any defaults?"},
            {"role": "user", "content": "no"},
        ],
        "product_info": "Web Dev",
        "cta": "Learn More",
        "landing_page": "https://www.example.com/",
        "email_length": "medium",
        "wants_follow_up": True,
        "follow_up_delay": {"value": 5, "unit": "minutes"},
        "skipped_fields": [
            EMAIL_LENGTH_FIELD,
            WANTS_FOLLOW_UP_FIELD,
            FOLLOW_UP_DELAY_FIELD,
            "campaign_name",
            "audience",
            "wants_cta",
            "cta",
            "landing_page",
        ],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("wants_cta") is True
    assert updates.get("cta") == "Learn More"
    assert updates.get("landing_page") == "https://www.example.com/"


@pytest.mark.asyncio
async def test_no_to_cta_sets_wants_cta_false_and_skips_label() -> None:
    llm = MagicMock()
    llm.extract_campaign_data = AsyncMock(
        return_value=CampaignData(product_info="Clerk"),
    )
    llm.generate = AsyncMock(return_value="Clerk Outreach")
    agent = CampaignCollectionAgent(llm=llm)
    workflow_repository.get_by_id = AsyncMock(return_value=None)
    workflow_repository.update_name = AsyncMock()
    state: ConversationState = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [
            {"role": "assistant", "content": "Do you want a CTA button?"},
            {"role": "user", "content": "no"},
        ],
        "product_info": "Clerk",
        "email_length": "medium",
        "wants_follow_up": True,
        "follow_up_delay": {"value": 2, "unit": "days"},
        "skipped_fields": [
            EMAIL_LENGTH_FIELD,
            WANTS_FOLLOW_UP_FIELD,
            FOLLOW_UP_DELAY_FIELD,
            "campaign_name",
            "audience",
        ],
    }
    updates = await agent.extract_and_update(state)
    assert updates.get("wants_cta") is False
    assert WANTS_CTA_FIELD in updates.get("skipped_fields", [])
    assert "cta" in updates.get("skipped_fields", [])
