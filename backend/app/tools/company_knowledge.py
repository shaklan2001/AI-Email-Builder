"""Company Knowledge Tool — answers product/company questions from campaign context."""

from __future__ import annotations

import re

from app.tools.base import ToolExecutionOutput, ToolRunContext


def _extract_company_query(message: str) -> str | None:
    patterns = (
        r"tell me more about\s+(.+?)(?:\.|$|\?)",
        r"more (?:info|information) (?:on|about)\s+(.+?)(?:\.|$|\?)",
        r"what (?:is|does)\s+(.+?)(?:\?|\.|$)",
        r"about\s+(.+?)(?:\.|$|\?)",
    )
    lowered = message.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if name and len(name) < 120:
                return name.title() if name.islower() else name
    return None


class CompanyKnowledgeTool:
    name = "company_knowledge"

    async def run(self, ctx: ToolRunContext) -> ToolExecutionOutput:
        queried = _extract_company_query(ctx.prospect_message)
        company_name = queried or ctx.company_name or ctx.campaign_name or "our company"

        sections: list[str] = []
        if ctx.product_info:
            sections.append(f"Product: {ctx.product_info}")
        if ctx.audience:
            sections.append(f"Audience: {ctx.audience}")
        if ctx.cta:
            sections.append(f"CTA: {ctx.cta}")
        if ctx.landing_page:
            sections.append(f"Learn more: {ctx.landing_page}")

        if not sections:
            sections.append(
                "We help teams automate outbound email workflows with AI-driven campaigns.",
            )

        body = "\n".join(sections)
        summary = f"Here is information about {company_name}:\n{body}"

        return ToolExecutionOutput(
            tool=self.name,
            summary=summary,
            data={
                "company_name": company_name,
                "product_info": ctx.product_info,
                "audience": ctx.audience,
                "cta": ctx.cta,
                "landing_page": ctx.landing_page,
                "sections": sections,
            },
        )


company_knowledge_tool = CompanyKnowledgeTool()
