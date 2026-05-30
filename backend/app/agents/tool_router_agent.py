"""Select which agent tool to invoke for a prospect message."""

from __future__ import annotations

import json
import re

from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.schemas.agent_tool import AGENT_TOOL_VALUES, AgentToolName
from app.schemas.reply_intent import ReplyIntent

_SYSTEM_PROMPT = """You route B2B sales email replies to the correct tool.

Tools:
- company_knowledge — prospect asks about the company, product, pricing, features, "tell me more about X"
- calendar_booking — prospect wants a demo, call, meeting, or to schedule time
- none — decline, unsubscribe, or no tool needed (simple thanks, etc.)

Respond with JSON only: {"tool": "company_knowledge" | "calendar_booking" | "none"}
"""

_COMPANY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:want|what)\s+to\s+know\b", re.IGNORECASE),
    re.compile(r"\bknow\s+\w+\s+about\b", re.IGNORECASE),
    re.compile(r"\blearn\s+more\s+about\b", re.IGNORECASE),
    re.compile(r"\babout\s+(?:the\s+|your\s+)?company\b", re.IGNORECASE),
)

_KEYWORD_RULES: tuple[tuple[tuple[str, ...], AgentToolName], ...] = (
    (
        (
            "book a demo",
            "get a demo",
            "schedule a call",
            "calendar",
            "meet next",
            "set up a call",
            "book demo",
            "want to try",
            "link of the tool",
        ),
        AgentToolName.CALENDAR_BOOKING,
    ),
    (
        (
            "tell me more",
            "more about",
            "more information",
            "what is",
            "about zylabs",
            "company info",
            "know more",
            "want to know",
            "about the company",
            "about your company",
            "about the product",
        ),
        AgentToolName.COMPANY_KNOWLEDGE,
    ),
)

_INTENT_TOOL_MAP: dict[ReplyIntent, AgentToolName] = {
    ReplyIntent.NEEDS_INFO: AgentToolName.COMPANY_KNOWLEDGE,
    ReplyIntent.QUESTION: AgentToolName.COMPANY_KNOWLEDGE,
    ReplyIntent.PRICING: AgentToolName.COMPANY_KNOWLEDGE,
    ReplyIntent.BOOK_DEMO: AgentToolName.CALENDAR_BOOKING,
}


class ToolRouterAgent:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        return get_groq_provider()

    @staticmethod
    def _parse_tool(raw: str) -> AgentToolName | None:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                value = data.get("tool")
                if isinstance(value, str) and value in AGENT_TOOL_VALUES:
                    return AgentToolName(value)
        except json.JSONDecodeError:
            pass
        lowered = cleaned.lower()
        if lowered in AGENT_TOOL_VALUES:
            return AgentToolName(lowered)
        return None

    @staticmethod
    def _matches_company_request(message: str) -> bool:
        for pattern in _COMPANY_PATTERNS:
            if pattern.search(message):
                return True
        return False

    @staticmethod
    def _keyword_route(message: str) -> AgentToolName:
        lowered = message.lower()
        for phrases, tool in _KEYWORD_RULES:
            if any(phrase in lowered for phrase in phrases):
                return tool
        if ToolRouterAgent._matches_company_request(message):
            return AgentToolName.COMPANY_KNOWLEDGE
        return AgentToolName.NONE

    @staticmethod
    def _intent_fallback(reply_intent: ReplyIntent | None) -> AgentToolName | None:
        if reply_intent is None:
            return None
        return _INTENT_TOOL_MAP.get(reply_intent)

    async def select_tool(
        self,
        *,
        prospect_message: str,
        reply_intent: ReplyIntent | None = None,
    ) -> AgentToolName:
        body = prospect_message.strip()
        if not body:
            return AgentToolName.NONE

        user_prompt = f"Prospect reply:\n{body}"
        if reply_intent is not None:
            user_prompt += f"\n\nClassified intent: {reply_intent.value}"

        try:
            llm = self._get_llm()
            raw = await llm.generate(_SYSTEM_PROMPT, user_prompt)
            parsed = self._parse_tool(raw)
            if parsed is not None and parsed != AgentToolName.NONE:
                return parsed
        except LLMProviderError:
            pass

        keyword_tool = self._keyword_route(body)
        if keyword_tool != AgentToolName.NONE:
            return keyword_tool

        intent_tool = self._intent_fallback(reply_intent)
        if intent_tool is not None:
            return intent_tool

        return AgentToolName.NONE


tool_router_agent = ToolRouterAgent()
