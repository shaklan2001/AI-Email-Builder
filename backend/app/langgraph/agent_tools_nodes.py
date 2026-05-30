from typing import Any

from app.agents.tool_router_agent import tool_router_agent
from app.langgraph.agent_tools_state import AgentToolsState
from app.schemas.agent_tool import AgentToolName
from app.schemas.reply_intent import ReplyIntent
from app.tools.base import ToolRunContext
from app.tools.registry import execute_agent_tool


def _tool_context(state: AgentToolsState) -> ToolRunContext:
    return ToolRunContext(
        workflow_id=str(state.get("workflow_id") or ""),
        lead_email=str(state.get("lead_email") or "").lower(),
        prospect_message=str(state.get("prospect_message") or ""),
        company_name=state.get("company_name"),
        product_info=state.get("product_info"),
        audience=state.get("audience"),
        cta=state.get("cta"),
        landing_page=state.get("landing_page"),
        campaign_name=state.get("campaign_name"),
    )


async def select_tool_node(state: AgentToolsState) -> dict[str, str]:
    raw_intent = state.get("reply_intent")
    reply_intent: ReplyIntent | None = None
    if isinstance(raw_intent, str) and raw_intent.strip():
        try:
            reply_intent = ReplyIntent(raw_intent.strip())
        except ValueError:
            reply_intent = None

    tool = await tool_router_agent.select_tool(
        prospect_message=str(state.get("prospect_message") or ""),
        reply_intent=reply_intent,
    )
    return {"selected_tool": tool.value}


async def execute_tool_node(state: AgentToolsState) -> dict[str, Any]:
    raw_tool = str(state.get("selected_tool") or AgentToolName.NONE.value)
    try:
        tool_name = AgentToolName(raw_tool)
    except ValueError:
        tool_name = AgentToolName.NONE

    if tool_name == AgentToolName.NONE:
        return {
            "tool_result": {},
            "agent_response": "",
        }

    output = await execute_agent_tool(tool_name, _tool_context(state))
    if output is None:
        return {
            "tool_result": {},
            "agent_response": "",
        }

    return {
        "tool_result": {
            "tool": output.tool,
            "summary": output.summary,
            "data": output.data,
        },
        "agent_response": output.summary,
    }
