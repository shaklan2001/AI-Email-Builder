"""Run LangGraph agent tools for prospect replies and persist execution history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.langgraph.agent_tools_graph import get_agent_tools_graph
from app.langgraph.agent_tools_state import AgentToolsState
from app.repositories.conversation_repository import conversation_repository
from app.repositories.tool_execution_repository import (
    ToolExecutionRepository,
    tool_execution_repository,
)
from app.schemas.agent_tool import AgentToolName


@dataclass
class AgentToolsRunResult:
    workflow_id: str
    lead_email: str
    selected_tool: AgentToolName
    tool_result: dict[str, Any]
    agent_response: str
    execution_id: str | None
    tool_called: bool


class AgentToolsService:
    def __init__(
        self,
        *,
        executions: ToolExecutionRepository | None = None,
    ) -> None:
        self._executions = executions or tool_execution_repository

    async def _campaign_context(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> dict[str, str | None]:
        state = await conversation_repository.get_conversation_state(user_id, workflow_id)
        if state is None:
            return {}
        return {
            "campaign_name": _str_field(state, "campaign_name"),
            "product_info": _str_field(state, "product_info"),
            "audience": _str_field(state, "audience"),
            "cta": _str_field(state, "cta"),
            "landing_page": _str_field(state, "landing_page"),
        }

    async def run_for_prospect_message(
        self,
        *,
        user_id: str,
        workflow_id: str,
        lead_email: str,
        prospect_message: str,
        inbound_reply_id: str | None = None,
    ) -> AgentToolsRunResult:
        context = await self._campaign_context(user_id=user_id, workflow_id=workflow_id)

        graph_state: AgentToolsState = {
            "workflow_id": workflow_id,
            "lead_email": lead_email.lower(),
            "prospect_message": prospect_message,
            "company_name": context.get("campaign_name"),
            "campaign_name": context.get("campaign_name"),
            "product_info": context.get("product_info"),
            "audience": context.get("audience"),
            "cta": context.get("cta"),
            "landing_page": context.get("landing_page"),
        }

        graph = get_agent_tools_graph()
        result_state = await graph.ainvoke(graph_state)

        raw_tool = str(result_state.get("selected_tool") or AgentToolName.NONE.value)
        try:
            selected_tool = AgentToolName(raw_tool)
        except ValueError:
            selected_tool = AgentToolName.NONE

        tool_result = result_state.get("tool_result")
        if not isinstance(tool_result, dict):
            tool_result = {}

        agent_response = str(result_state.get("agent_response") or "")
        tool_called = selected_tool != AgentToolName.NONE and bool(tool_result)

        execution_id: str | None = None
        if tool_called or selected_tool != AgentToolName.NONE:
            record = await self._executions.create(
                workflow_id=workflow_id,
                lead_email=lead_email,
                tool_name=selected_tool,
                prospect_message=prospect_message,
                result=tool_result,
                agent_response=agent_response,
                inbound_reply_id=inbound_reply_id,
            )
            execution_id = record.id

        return AgentToolsRunResult(
            workflow_id=workflow_id,
            lead_email=lead_email.lower(),
            selected_tool=selected_tool,
            tool_result=tool_result,
            agent_response=agent_response,
            execution_id=execution_id,
            tool_called=tool_called,
        )

    async def list_executions(self, workflow_id: str, *, limit: int = 50):
        return await self._executions.list_for_workflow(workflow_id, limit=limit)


def _str_field(state: dict[str, object], key: str) -> str | None:
    value = state.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


agent_tools_service = AgentToolsService()
