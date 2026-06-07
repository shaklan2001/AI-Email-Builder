"""Parse user preferences for email length and follow-up opt-in during collection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

EmailLength = Literal["short", "medium", "long"]


@dataclass(frozen=True)
class ParsedEmailLength:
    category: EmailLength
    words: int | None = None

EMAIL_LENGTH_QUESTION = (
    "How long should the initial outreach email be?\n\n"
    "• Short (about 50–80 words)\n"
    "• Medium (about 100–150 words)\n"
    "• Long (about 200+ words)"
)

WANTS_FOLLOW_UP_QUESTION = (
    "If a recipient does not reply, should I send a follow-up email?\n\n"
    "Reply yes to include a follow-up, or no to send only the initial email."
)

WANTS_CTA_QUESTION = (
    "Do you want a call-to-action button in the email?\n\n"
    "Reply yes to add one, or no to skip the button."
)

CTA_LABEL_QUESTION = (
    "What should the CTA button say?\n\n"
    "Examples: Learn More, Book a Call, Book a Demo, Get Started."
)

_DEFAULT_EMAIL_LENGTH: EmailLength = "medium"

_LENGTH_ALIASES: dict[EmailLength, tuple[str, ...]] = {
    "short": ("short", "brief", "concise", "quick", "small", "tiny"),
    "medium": ("medium", "moderate", "standard", "normal", "average"),
    "long": ("long", "detailed", "lengthy", "extended", "comprehensive"),
}

_YES_PHRASES: tuple[str, ...] = (
    "yes",
    "yeah",
    "yep",
    "yup",
    "sure",
    "please",
    "definitely",
    "absolutely",
    "of course",
    "i do",
    "i want",
    "send follow",
    "need follow",
    "include follow",
    "with follow",
)

_NO_PHRASES: tuple[str, ...] = (
    "no",
    "nope",
    "nah",
    "don't",
    "dont",
    "do not",
    "no need",
    "not needed",
    "no follow",
    "skip follow",
    "without follow",
    "only initial",
    "just one email",
    "single email",
    "one email only",
)


def default_email_length() -> EmailLength:
    return _DEFAULT_EMAIL_LENGTH


def _words_to_category(words: int) -> EmailLength:
    if words <= 80:
        return "short"
    if words <= 150:
        return "medium"
    return "long"


def format_email_length_brief(
    length: str | None,
    *,
    words: int | None = None,
) -> str:
    labels = {"short": "Short", "medium": "Medium", "long": "Long"}
    if words is not None and words > 0:
        label = labels.get((length or "").strip().lower(), "")
        if label:
            return f"{words} words ({label})"
        return f"{words} words"
    if not length:
        return "Medium"
    return labels.get(length.strip().lower(), length.strip().title())


def format_wants_follow_up_brief(wants_follow_up: bool | None) -> str:
    if wants_follow_up is True:
        return "Yes — send follow-up if no reply"
    if wants_follow_up is False:
        return "No — initial email only"
    return "Not provided"


def format_wants_cta_brief(wants_cta: bool | None) -> str:
    if wants_cta is True:
        return "Yes — include a CTA button"
    if wants_cta is False:
        return "No — no CTA button"
    return "Not provided"


def parse_email_length_detail(text: str) -> ParsedEmailLength | None:
    cleaned = text.strip().lower()
    if not cleaned:
        return None

    for length, aliases in _LENGTH_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", cleaned) for alias in aliases):
            return ParsedEmailLength(category=length)

    word_match = re.search(r"\b(\d+)\s*(?:words?|w)?\b", cleaned)
    if word_match:
        words = int(word_match.group(1))
        if 20 <= words <= 2000:
            return ParsedEmailLength(category=_words_to_category(words), words=words)

    bare_number = re.fullmatch(r"(\d+)", cleaned)
    if bare_number:
        words = int(bare_number.group(1))
        if 20 <= words <= 2000:
            return ParsedEmailLength(category=_words_to_category(words), words=words)

    return None


def parse_email_length(text: str) -> EmailLength | None:
    parsed = parse_email_length_detail(text)
    return parsed.category if parsed is not None else None


_FOLLOW_UP_ENABLE_INTENT = re.compile(
    r"(?:want|need|add|include|send)\b.{0,50}follow[\s-]?(?:up|email)",
    re.IGNORECASE,
)
_FOLLOW_UP_ON_NO_REPLY = re.compile(
    r"follow[\s-]?(?:up|email).{0,80}(?:if|when).{0,40}"
    r"(?:no\s+reply|not\s+reply|do(?:es)?n'?t\s+reply|don'?t\s+reply)",
    re.IGNORECASE,
)
_NO_REPLY_CONDITION = re.compile(
    r"(?:if|when).{0,40}(?:no\s+reply|not\s+reply|do(?:es)?\s+not\s+reply|don'?t\s+reply)",
    re.IGNORECASE,
)


def is_follow_up_enable_intent(text: str) -> bool:
    """True when the user is asking to include a no-reply follow-up email."""
    cleaned = text.strip()
    if not cleaned:
        return False
    if _FOLLOW_UP_ENABLE_INTENT.search(cleaned):
        return True
    if _FOLLOW_UP_ON_NO_REPLY.search(cleaned):
        return True
    if re.search(r"follow[\s-]?(?:up|email)", cleaned, re.IGNORECASE) and _NO_REPLY_CONDITION.search(
        cleaned,
    ):
        return True
    return False


def follow_up_prefs_from_brief_dict(
    brief: dict[str, object],
) -> tuple[bool | None, object]:
    """Read follow-up preference and delay encoded in the campaign brief snapshot."""
    from app.services.follow_up_delay import parse_follow_up_delay

    enabled = str(brief.get("followUpEnabled") or brief.get("follow_up_enabled") or "")
    lower = enabled.lower()
    wants: bool | None = None
    if "yes" in lower and "follow" in lower:
        wants = True
    elif "no" in lower and "initial" in lower:
        wants = False

    delay = None
    raw_delay = brief.get("followUpDelay") or brief.get("follow_up_delay")
    if isinstance(raw_delay, str) and raw_delay.strip():
        normalized = raw_delay.strip().lower()
        if "none" not in normalized and "initial email only" not in normalized:
            delay = parse_follow_up_delay(raw_delay)

    return wants, delay


def parse_wants_follow_up(text: str) -> bool | None:
    cleaned = text.strip().lower()
    if not cleaned:
        return None

    if is_follow_up_enable_intent(text):
        return True

    for phrase in _NO_PHRASES:
        if phrase not in cleaned:
            continue
        if phrase in ("do not", "dont", "don't") and _NO_REPLY_CONDITION.search(cleaned):
            continue
        return False
    if cleaned in ("n", "no."):
        return False

    if any(phrase in cleaned for phrase in _YES_PHRASES):
        return True
    if cleaned in ("y", "yes."):
        return True

    return None


def email_length_instructions(
    length: str | None,
    *,
    words: int | None = None,
) -> str:
    if words is not None and words > 0:
        return f"Target about {words} words for the email body (plain text)."
    resolved = (length or _DEFAULT_EMAIL_LENGTH).strip().lower()
    guidance = {
        "short": "Keep the email SHORT: about 50–80 words, 2–3 short paragraphs max.",
        "medium": "Keep the email MEDIUM length: about 100–150 words.",
        "long": "Write a LONGER email: about 200+ words with more detail and context.",
    }
    return guidance.get(resolved, guidance["medium"])
