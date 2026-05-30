from typing import Any, TypedDict


class AgentToolsState(TypedDict, total=False):
    workflow_id: str
    lead_email: str
    prospect_message: str
    reply_intent: str | None
    company_name: str | None
    product_info: str | None
    audience: str | None
    cta: str | None
    landing_page: str | None
    campaign_name: str | None
    selected_tool: str
    tool_result: dict[str, Any]
    agent_response: str
