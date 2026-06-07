"""Company Knowledge Tool — answers product/company questions from campaign context."""

from __future__ import annotations

import re

from app.tools.base import ToolExecutionOutput, ToolRunContext

_GENERIC_QUERY_TARGETS = frozenset(
    {
        "it",
        "this",
        "that",
        "them",
        "these",
        "those",
        "more",
        "info",
        "information",
        "the product",
        "your product",
        "the company",
        "your company",
        "the service",
        "your service",
        "the crm",
        "the tool",
        "the software",
        "the platform",
    }
)


def _extract_company_query(message: str) -> str | None:
    patterns = (
        r"tell me more about\s+(.+?)(?:\.|$|\?)",
        r"more (?:info|information) (?:on|about)\s+(.+?)(?:\.|$|\?)",
        r"(?:want|what)\s+to\s+know\s+(?:mo\w+\s+)?about\s+(.+?)(?:\.|$|\?)",
        r"know\s+\w+\s+about\s+(.+?)(?:\.|$|\?)",
        r"what (?:is|does)\s+(.+?)(?:\?|\.|$)",
        r"about\s+(?:the\s+|your\s+)?(.+?)(?:\.|$|\?)",
    )
    lowered = message.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if name and len(name) < 120 and not _is_generic_query_target(name):
                return name.title() if name.islower() else name
    return None


def _is_generic_query_target(name: str) -> bool:
    cleaned = name.strip().lower()
    if not cleaned:
        return True
    if cleaned in _GENERIC_QUERY_TARGETS:
        return True
    if len(cleaned) <= 3:
        return True
    if cleaned.startswith(("the ", "your ", "a ")):
        return True
    return False


def _resolve_company_name(ctx: ToolRunContext, queried: str | None) -> str:
    """Prefer campaign context over pronouns extracted from the prospect reply."""
    if queried and not _is_generic_query_target(queried):
        return queried

    for candidate in (ctx.campaign_name, ctx.company_name):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    if isinstance(ctx.product_info, str) and ctx.product_info.strip():
        product = ctx.product_info.strip()
        first_sentence = re.split(r"[.!?\n]", product, maxsplit=1)[0].strip()
        if first_sentence:
            return first_sentence

    return "our company"


def _resolve_product_line(ctx: ToolRunContext) -> str:
    if isinstance(ctx.product_info, str) and ctx.product_info.strip():
        return ctx.product_info.strip()
    return "AI-powered sales outreach automation"


class CompanyKnowledgeTool:
    name = "company_knowledge"

    async def run(self, ctx: ToolRunContext) -> ToolExecutionOutput:
        queried = _extract_company_query(ctx.prospect_message)
        company_name = _resolve_company_name(ctx, queried)
        product_line = _resolve_product_line(ctx)
        audience_line = ctx.audience or "B2B sales and marketing teams"
        cta_line = ctx.cta or "Book a demo"
        website = ctx.landing_page or "https://example.com"

        pricing = (
            "Starter: $49/mo for up to 500 leads. "
            "Growth: $149/mo with AI reply agent and calendar booking. "
            "Enterprise: custom pricing with dedicated support."
        )
        faqs = (
            "Q: How fast can I launch a campaign?\n"
            "A: Most teams go live in under 10 minutes via chat.\n\n"
            "Q: Does the AI reply automatically?\n"
            "A: Yes — up to 2 auto-replies, then human review is flagged.\n\n"
            "Q: Which email provider do you use?\n"
            "A: Resend with full open, click, and reply tracking."
        )
        case_studies = (
            "Case study — SaaS outbound: 34% reply rate lift after switching to AI follow-ups.\n"
            "Case study — Hardware launch: 120 demo bookings in 30 days from homeowner outreach."
        )

        summary = (
            f"Here is information about {company_name}:\n\n"
            f"Company: {company_name}\n"
            f"Product: {product_line}\n"
            f"Audience: {audience_line}\n"
            f"CTA: {cta_line}\n"
            f"Website: {website}\n\n"
            f"Pricing:\n{pricing}\n\n"
            f"FAQs:\n{faqs}\n\n"
            f"Case studies:\n{case_studies}"
        )

        return ToolExecutionOutput(
            tool=self.name,
            summary=summary,
            data={
                "company_name": company_name,
                "product_info": product_line,
                "audience": audience_line,
                "cta": cta_line,
                "landing_page": website,
                "pricing": pricing,
                "faqs": faqs,
                "case_studies": case_studies,
            },
        )


company_knowledge_tool = CompanyKnowledgeTool()
