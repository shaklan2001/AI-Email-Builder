"""Tests for LangGraph agent tools (spec 44)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.tool_router_agent import ToolRouterAgent
from app.providers.llm.base import LLMProviderError
from app.schemas.agent_tool import AgentToolName
from app.services.agent_tools_service import AgentToolsService
from app.tools.calendar_booking import CalendarBookingTool
from app.tools.company_knowledge import CompanyKnowledgeTool
from app.tools.base import ToolRunContext


def _ctx(*, message: str) -> ToolRunContext:
    return ToolRunContext(
        workflow_id="wf_1",
        lead_email="lead@example.com",
        prospect_message=message,
        company_name="ZyLabs",
        product_info="AI email automation platform",
        audience="B2B SaaS founders",
        cta="Book a demo",
        landing_page="https://zylabs.example.com",
        campaign_name="ZyLabs Launch",
    )


@pytest.mark.asyncio
async def test_company_knowledge_tool_zylabs_query() -> None:
    tool = CompanyKnowledgeTool()
    output = await tool.run(_ctx(message="Tell me more about ZyLabs"))
    assert output.tool == "company_knowledge"
    assert "ZyLabs" in output.summary or "zylabs" in output.summary.lower()
    assert output.data.get("product_info") == "AI email automation platform"
    assert output.data.get("landing_page") == "https://zylabs.example.com"


@pytest.mark.asyncio
async def test_company_knowledge_ignores_pronoun_and_uses_campaign_context() -> None:
    tool = CompanyKnowledgeTool()
    output = await tool.run(
        ToolRunContext(
            workflow_id="wf_1",
            lead_email="lead@example.com",
            prospect_message="i like to knwo more about it",
            company_name="sinch converse",
            product_info="new CRM product designed for general customers",
            audience="General Customers",
            cta="Learn More",
            landing_page="https://sinch.example.com",
            campaign_name="sinch converse",
        ),
    )
    assert output.data.get("company_name") == "sinch converse"
    assert "It" not in output.summary
    assert "new CRM product" in output.summary
    assert output.data.get("audience") == "General Customers"
    assert output.data.get("cta") == "Learn More"


@pytest.mark.asyncio
async def test_calendar_booking_tool_demo_request() -> None:
    tool = CalendarBookingTool()
    output = await tool.run(_ctx(message="Book a demo next week"))
    assert output.tool == "calendar_booking"
    assert "nishantshaklan.co.in" in output.data["booking_url"]
    assert "wf_1" in output.data["booking_url"]
    assert "demo" in output.summary.lower() or "calendar" in output.summary.lower()


@pytest.mark.asyncio
async def test_tool_router_keyword_routes() -> None:
    llm = MagicMock()
    llm.generate = AsyncMock(side_effect=LLMProviderError("offline"))
    router = ToolRouterAgent(llm=llm)

    assert await router.select_tool(prospect_message="Tell me more about ZyLabs") == (
        AgentToolName.COMPANY_KNOWLEDGE
    )
    assert await router.select_tool(prospect_message="Book a demo next week") == (
        AgentToolName.CALENDAR_BOOKING
    )


@pytest.mark.asyncio
async def test_agent_tools_service_runs_graph_and_stores_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executions = AsyncMock()
    executions.create = AsyncMock(
        return_value=MagicMock(id="exec_1"),
    )

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "selected_tool": AgentToolName.COMPANY_KNOWLEDGE.value,
            "tool_result": {
                "tool": "company_knowledge",
                "summary": "Here is information about ZyLabs.",
                "data": {"company_name": "ZyLabs"},
            },
            "agent_response": "Here is information about ZyLabs.",
        },
    )

    monkeypatch.setattr(
        "app.services.agent_tools_service.get_agent_tools_graph",
        lambda: mock_graph,
    )
    monkeypatch.setattr(
        "app.services.agent_tools_service.conversation_repository.get_conversation_state",
        AsyncMock(
            return_value={
                "campaign_name": "ZyLabs",
                "product_info": "AI platform",
            },
        ),
    )

    service = AgentToolsService(executions=executions)
    result = await service.run_for_prospect_message(
        user_id="user_1",
        workflow_id="wf_1",
        lead_email="lead@example.com",
        prospect_message="Tell me more about ZyLabs",
    )

    assert result.tool_called is True
    assert result.selected_tool == AgentToolName.COMPANY_KNOWLEDGE
    assert "ZyLabs" in result.agent_response
    assert result.tool_result.get("tool") == "company_knowledge"
    assert result.execution_id == "exec_1"
    executions.create.assert_called_once()
