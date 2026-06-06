"""Inbound reply normalization."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.reply_intent_agent import ReplyIntentAgent
from app.agents.tool_router_agent import ToolRouterAgent
from app.providers.llm.base import LLMProviderError
from app.schemas.agent_tool import AgentToolName
from app.schemas.reply_intent import ReplyIntent
from app.services.reply_handling_service import extract_reply_text, webhook_has_reply_body
from app.services.reply_text import normalize_prospect_reply, strip_quoted_reply_body


def test_webhook_payload_without_body_does_not_use_subject_as_body() -> None:
    data = {
        "from": "lead@example.com",
        "subject": "Re: Introducing cursor ai - streamline your workflow",
        "email_id": "3580e78e-8023-4896-94a0-94091402646d",
    }
    assert webhook_has_reply_body(data) is False
    assert extract_reply_text(data) == ""


def test_normalize_rejects_subject_only_payload() -> None:
    subject = "Re: Introducing cursor ai - streamline your workflow"
    assert normalize_prospect_reply(subject, subject=subject) == ""


def test_strip_demo_reply_from_quoted_thread() -> None:
    raw = (
        "Its look nice can i get a demo or link of the tool i want to try it and use it\n\n"
        "On Fri, 5 Jun 2026 at 6:19 PM, <onboarding@resend.dev> wrote:\n"
        "> Hi there,"
    )
    assert (
        strip_quoted_reply_body(raw)
        == "Its look nice can i get a demo or link of the tool i want to try it and use it"
    )


def test_strip_quoted_reply_body_keeps_prospect_message_only() -> None:
    raw = (
        "I what to know moew about the company\n\n"
        "On Fri, Jun 6, 2025 at 5:52 PM onboarding@resend.dev wrote:\n"
        "> Introducing cursor ai"
    )
    assert strip_quoted_reply_body(raw) == "I what to know moew about the company"


def test_normalize_prospect_reply_prefers_body_over_subject() -> None:
    assert (
        normalize_prospect_reply(
            "Tell me more about ZyLabs",
            subject="Re: Introducing cursor ai",
        )
        == "Tell me more about ZyLabs"
    )


@pytest.mark.asyncio
async def test_typo_reply_classifies_as_needs_info_without_llm() -> None:
    llm = MagicMock()
    llm.generate = AsyncMock(side_effect=LLMProviderError("offline"))
    agent = ReplyIntentAgent(llm=llm)

    intent = await agent.classify(
        reply_body="I what to know moew about the company",
    )

    assert intent == ReplyIntent.NEEDS_INFO


@pytest.mark.asyncio
async def test_typo_reply_routes_to_company_knowledge_without_llm() -> None:
    llm = MagicMock()
    llm.generate = AsyncMock(side_effect=LLMProviderError("offline"))
    router = ToolRouterAgent(llm=llm)

    tool = await router.select_tool(
        prospect_message="I what to know moew about the company",
        reply_intent=ReplyIntent.NEEDS_INFO,
    )

    assert tool == AgentToolName.COMPANY_KNOWLEDGE


@pytest.mark.asyncio
async def test_demo_request_routes_to_calendar_booking_without_llm() -> None:
    llm = MagicMock()
    llm.generate = AsyncMock(side_effect=LLMProviderError("offline"))
    router = ToolRouterAgent(llm=llm)

    tool = await router.select_tool(
        prospect_message=(
            "Its look nice can i get a demo or link of the tool "
            "i want to try it and use it"
        ),
        reply_intent=ReplyIntent.BOOK_DEMO,
    )

    assert tool == AgentToolName.CALENDAR_BOOKING
