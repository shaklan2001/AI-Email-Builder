"""User actions on the campaign brief (spec 15.2)."""

from __future__ import annotations

import re
from typing import Literal

BriefUserAction = Literal["approve", "edit"]

_APPROVE_EXACT = frozenset(
    {
        "looks good",
        "looks good to me",
        "look good",
        "look good to me",
        "approve",
        "approved",
        "all good",
        "good to go",
        "go ahead",
        "let's go",
        "lets go",
        "perfect",
        "sounds good",
    },
)

_APPROVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:now|yes|yep|yeah|ok(?:ay)?|sure),?\s+(?:it\s+)?(?:looks?|look)\s+good\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:it\s+)?(?:looks?|look)\s+good(?:\s+now)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:it\s+)?(?:looks?|look)\s+cool(?:\s+now)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\beverything(?:'s|\s+is)?\s+(?:looks?|look)\s+(?:good|cool|great|fine)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:i(?:'m| am)\s+)?(?:happy|good)\s+with\s+(?:it|this|the brief)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:no\s+)?(?:changes?|edits?)\s+(?:needed|required)\b", re.IGNORECASE),
    re.compile(r"\bready\s+to\s+(?:go|proceed|approve)\b", re.IGNORECASE),
    re.compile(r"\ball\s+set\b", re.IGNORECASE),
)

_EDIT_EXACT = frozenset(
    {
        "edit campaign details",
        "edit campaign detail",
        "edit details",
    },
)


def is_brief_approval_message(message: str) -> bool:
    """True when the user is approving the campaign brief (chat or button)."""
    normalized = message.strip().lower().rstrip(".!")
    if not normalized:
        return False
    if normalized in _APPROVE_EXACT:
        return True
    return any(pattern.search(normalized) for pattern in _APPROVE_PATTERNS)


def parse_brief_user_action(message: str) -> BriefUserAction | None:
    if is_brief_approval_message(message):
        return "approve"
    normalized = message.strip().lower().rstrip(".!")
    if normalized in _EDIT_EXACT:
        return "edit"
    return None
