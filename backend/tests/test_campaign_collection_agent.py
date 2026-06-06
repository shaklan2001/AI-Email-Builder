"""Campaign collection agent — skip/delegate, missing_fields, no repeat questions."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.campaign_collection_agent import CampaignCollectionAgent
from app.langgraph.state import ConversationState
from app.schemas.campaign import CampaignData
from app.services.campaign_field_policy import (
    EMAIL_LENGTH_FIELD,
    REQUIRED_FIELD,
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
