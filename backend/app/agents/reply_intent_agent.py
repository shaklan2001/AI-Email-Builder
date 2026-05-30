"""Classify inbound email replies into sales intents."""

from __future__ import annotations

import json
import re

from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.schemas.reply_intent import REPLY_INTENT_ALIASES, REPLY_INTENT_VALUES, ReplyIntent

_SYSTEM_PROMPT = """You classify B2B sales email replies into exactly one intent.

Allowed values only:
- interested — wants to proceed, positive, asking to learn more in a buying sense
- not_interested — declines, not a fit (but not explicit unsubscribe)
- needs_info — asks questions, wants details/docs before deciding
- book_demo — wants a call, demo, meeting, calendar link
- pricing — asks about cost, pricing, budget, plans
- question — general product question not covered by pricing or demo
- unsubscribe — explicit opt-out: unsubscribe, stop emailing, remove me
- unknown — cannot classify confidently

Respond with JSON only: {"intent": "<one of the eight values>"}
"""

_INFO_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:want|what)\s+to\s+know\b", re.IGNORECASE),
    re.compile(r"\bknow\s+\w+\s+about\b", re.IGNORECASE),
    re.compile(r"\blearn\s+more\s+about\b", re.IGNORECASE),
    re.compile(r"\babout\s+(?:the\s+|your\s+)?company\b", re.IGNORECASE),
    re.compile(r"\bmore\s+(?:info|information)\b", re.IGNORECASE),
)

_KEYWORD_RULES: tuple[tuple[tuple[str, ...], ReplyIntent], ...] = (
    (
        ("unsubscribe", "remove me", "stop emailing", "opt out", "opt-out"),
        ReplyIntent.UNSUBSCRIBE,
    ),
    (
        ("not interested", "no thanks", "not a fit", "pass for now"),
        ReplyIntent.NOT_INTERESTED,
    ),
    (
        (
            "book a demo",
            "get a demo",
            "schedule a call",
            "calendar",
            "meet next",
            "set up a call",
            "want to try",
            "link of the tool",
        ),
        ReplyIntent.BOOK_DEMO,
    ),
    (
        ("pricing", "how much", "cost", "price", "budget", "plans"),
        ReplyIntent.PRICING,
    ),
    (
        (
            "tell me more",
            "more information",
            "more about",
            "details",
            "send info",
            "how does",
            "know more",
            "want to know",
            "about the company",
            "about your company",
        ),
        ReplyIntent.NEEDS_INFO,
    ),
    (
        ("interested", "sounds good", "let's do it", "yes please", "would love to"),
        ReplyIntent.INTERESTED,
    ),
)


class ReplyIntentAgent:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        return get_groq_provider()

    @staticmethod
    def _coerce_intent(value: str) -> ReplyIntent | None:
        lowered = value.strip().lower()
        if lowered in REPLY_INTENT_VALUES:
            return ReplyIntent(lowered)
        return REPLY_INTENT_ALIASES.get(lowered)

    @staticmethod
    def _parse_intent(raw: str) -> ReplyIntent | None:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                value = data.get("intent")
                if isinstance(value, str):
                    return ReplyIntentAgent._coerce_intent(value)
        except json.JSONDecodeError:
            pass
        return ReplyIntentAgent._coerce_intent(cleaned)

    @staticmethod
    def _matches_info_request(text: str) -> bool:
        for pattern in _INFO_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @staticmethod
    def _keyword_classify(text: str) -> ReplyIntent:
        lowered = text.lower()
        for phrases, intent in _KEYWORD_RULES:
            if any(phrase in lowered for phrase in phrases):
                return intent
        if ReplyIntentAgent._matches_info_request(text):
            return ReplyIntent.NEEDS_INFO
        if "?" in text:
            return ReplyIntent.QUESTION
        if any(token in lowered for token in ("company", "product", "pricing", "feature")):
            return ReplyIntent.QUESTION
        return ReplyIntent.UNKNOWN

    async def classify(
        self,
        *,
        reply_body: str,
        reply_subject: str | None = None,
        product_context: str | None = None,
    ) -> ReplyIntent:
        body = reply_body.strip()
        if not body and reply_subject:
            body = reply_subject.strip()
        if not body:
            return ReplyIntent.UNKNOWN

        user_parts = [f"Reply body:\n{body}"]
        if reply_subject:
            user_parts.insert(0, f"Subject: {reply_subject}")
        if product_context:
            user_parts.append(f"Campaign context: {product_context}")
        user_prompt = "\n\n".join(user_parts)

        try:
            llm = self._get_llm()
            raw = await llm.generate(_SYSTEM_PROMPT, user_prompt)
            parsed = self._parse_intent(raw)
            if parsed is not None and parsed != ReplyIntent.UNKNOWN:
                return parsed
        except LLMProviderError:
            pass

        return self._keyword_classify(body)


reply_intent_agent = ReplyIntentAgent()
