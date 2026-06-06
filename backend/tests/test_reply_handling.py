"""Tests for inbound reply handling (spec 37)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.reply_intent_agent import ReplyIntentAgent
from app.providers.llm.base import LLMProviderError
from app.repositories.inbound_reply_repository import InboundReplyRecord
from app.repositories.lead_repository import LeadRecord, lead_status_for_reply_intent
from app.schemas.enums import LeadStatus
from app.schemas.reply_intent import ReplyIntent
from app.schemas.agent_tool import AgentToolName
from app.services.agent_tools_service import AgentToolsRunResult
from app.services.reply_handling_service import (
    ReplyHandlingService,
    extract_reply_subject,
    extract_reply_text,
)


@pytest.mark.parametrize(
    ("intent", "expected_status"),
    [
        (ReplyIntent.INTERESTED, LeadStatus.INTERESTED),
        (ReplyIntent.NOT_INTERESTED, LeadStatus.NOT_INTERESTED),
        (ReplyIntent.NEED_MORE_INFO, LeadStatus.REPLIED),
        (ReplyIntent.BOOK_DEMO, LeadStatus.BOOKED_DEMO),
    ],
)
def test_lead_status_mapping(intent: ReplyIntent, expected_status: LeadStatus) -> None:
    assert lead_status_for_reply_intent(intent) == expected_status


def test_extract_reply_text_prefers_body_fields() -> None:
    data = {"subject": "Re: Hi", "text": "Sounds good, let's talk."}
    assert extract_reply_text(data) == "Re: Hi\n\nSounds good, let's talk."


def test_extract_reply_subject() -> None:
    assert extract_reply_subject({"subject": "  Re: Demo  "}) == "Re: Demo"
    assert extract_reply_subject({}) is None


@pytest.mark.asyncio
async def test_reply_intent_agent_keyword_fallback() -> None:
    llm = MagicMock()
    llm.generate = AsyncMock(side_effect=LLMProviderError("offline"))
    agent = ReplyIntentAgent(llm=llm)
    assert await agent.classify(reply_body="Please unsubscribe me") == ReplyIntent.NOT_INTERESTED
    assert await agent.classify(reply_body="Can we book a demo next week?") == ReplyIntent.BOOK_DEMO
    assert await agent.classify(reply_body="Send pricing details") == ReplyIntent.NEED_MORE_INFO
    assert await agent.classify(reply_body="Yes, very interested!") == ReplyIntent.INTERESTED


@pytest.mark.asyncio
async def test_reply_handling_service_classifies_and_persists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)
    leads = AsyncMock()
    leads.upsert_for_workflow = AsyncMock(
        return_value=LeadRecord(
            id="lead_1",
            workflow_id="wf_1",
            email="lead@example.com",
            campaign_id="wf_1",
            status=LeadStatus.INTERESTED.value,
            reply_intent=ReplyIntent.INTERESTED.value,
            last_reply_body="Yes please",
            updated_at=now,
            created_at=now,
        ),
    )
    inbound = AsyncMock()
    inbound.create = AsyncMock(
        return_value=InboundReplyRecord(
            id="ir_1",
            workflow_id="wf_1",
            lead_email="lead@example.com",
            reply_intent=ReplyIntent.INTERESTED.value,
            reply_body="Yes please",
            reply_subject="Re: Hello",
            webhook_event_id="wh_1",
            created_at=now,
        ),
    )

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "reply_intent": ReplyIntent.INTERESTED.value,
            "lead_status": LeadStatus.INTERESTED.value,
        },
    )

    monkeypatch.setattr(
        "app.services.reply_handling_service.get_reply_handling_graph",
        lambda: mock_graph,
    )
    monkeypatch.setattr(
        "app.services.reply_handling_service.conversation_repository.get_campaign_state",
        AsyncMock(return_value=None),
    )

    agent_tools = AsyncMock()
    agent_tools.run_for_prospect_message = AsyncMock(
        return_value=AgentToolsRunResult(
            workflow_id="wf_1",
            lead_email="lead@example.com",
            selected_tool=AgentToolName.NONE,
            tool_result={},
            agent_response="",
            execution_id=None,
            tool_called=False,
        ),
    )
    email_svc = MagicMock()
    email_svc.send_email = AsyncMock()

    service = ReplyHandlingService(
        leads=leads,
        inbound_replies=inbound,
        agent_tools=agent_tools,
        email=email_svc,
    )
    result = await service.process_inbound_reply(
        user_id="user_1",
        workflow_id="wf_1",
        lead_email="Lead@Example.com",
        reply_body="Yes please",
        reply_subject="Re: Hello",
        webhook_event_id="wh_1",
    )

    assert result.reply_intent == ReplyIntent.INTERESTED
    assert result.lead_status == LeadStatus.INTERESTED
    assert result.lead_updated is True
    assert result.reply_stored is True
    inbound.create.assert_called_once()
    leads.upsert_for_workflow.assert_called_once()
