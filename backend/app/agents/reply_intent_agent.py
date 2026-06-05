"""Classify inbound email replies into sales intents."""

from __future__ import annotations

import json
import re

from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.schemas.reply_intent import REPLY_INTENT_VALUES, ReplyIntent

_SYSTEM_PROMPT = """You classify B2B sales email replies into exactly one intent.

Allowed values only:
- interested — wants to proceed, positive, asking to learn more in a buying sense
- not_interested — declines, unsubscribe, stop emailing, not a fit
- need_more_info — asks questions, wants pricing/details/docs before deciding
- book_demo — wants a call, demo, meeting, calendar link

Respond with JSON only: {"intent": "<one of the four values>"}
"""

_KEYWORD_RULES: tuple[tuple[tuple[str, ...], ReplyIntent], ...] = (
    (("unsubscribe", "not interested", "no thanks", "stop emailing", "remove me"), ReplyIntent.NOT_INTERESTED),
    (("book a demo", "schedule a call", "calendar", "meet next", "book_demo", "set up a call"), ReplyIntent.BOOK_DEMO),
    (("tell me more", "more information", "pricing", "how much", "details", "send info"), ReplyIntent.NEED_MORE_INFO),
    (("interested", "sounds good", "let's do it", "yes please", "would love to"), ReplyIntent.INTERESTED),
)


class ReplyIntentAgent:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        return get_groq_provider()

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
                if isinstance(value, str) and value in REPLY_INTENT_VALUES:
                    return ReplyIntent(value)
        except json.JSONDecodeError:
            pass
        lowered = cleaned.lower()
        if lowered in REPLY_INTENT_VALUES:
            return ReplyIntent(lowered)
        return None

    @staticmethod
    def _keyword_classify(text: str) -> ReplyIntent:
        lowered = text.lower()
        for phrases, intent in _KEYWORD_RULES:
            if any(phrase in lowered for phrase in phrases):
                return intent
        return ReplyIntent.NEED_MORE_INFO

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
            return ReplyIntent.NEED_MORE_INFO

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
            if parsed is not None:
                return parsed
        except LLMProviderError:
            pass

        return self._keyword_classify(body)


reply_intent_agent = ReplyIntentAgent()
