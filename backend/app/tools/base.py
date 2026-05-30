from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolRunContext:
    workflow_id: str
    lead_email: str
    prospect_message: str
    company_name: str | None
    product_info: str | None
    audience: str | None
    cta: str | None
    landing_page: str | None
    campaign_name: str | None


@dataclass(frozen=True)
class ToolExecutionOutput:
    tool: str
    summary: str
    data: dict[str, Any]
