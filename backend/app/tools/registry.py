from app.schemas.agent_tool import AgentToolName
from app.tools.base import ToolExecutionOutput, ToolRunContext
from app.tools.calendar_booking import calendar_booking_tool
from app.tools.company_knowledge import company_knowledge_tool


async def execute_agent_tool(
    tool_name: AgentToolName,
    ctx: ToolRunContext,
) -> ToolExecutionOutput | None:
    if tool_name == AgentToolName.COMPANY_KNOWLEDGE:
        return await company_knowledge_tool.run(ctx)
    if tool_name == AgentToolName.CALENDAR_BOOKING:
        return await calendar_booking_tool.run(ctx)
    return None
