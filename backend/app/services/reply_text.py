"""Normalize inbound reply bodies before intent classification and tool routing."""

from __future__ import annotations

import re

# Common quoted-reply separators (order matters — more specific first).
_QUOTE_SPLIT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\nOn .+?wrote:\s*\n", re.IGNORECASE | re.DOTALL),
    re.compile(r"\n-{2,}\s*Original Message\s*-{2,}\s*\n", re.IGNORECASE),
    re.compile(r"\nFrom:\s*.+\n", re.IGNORECASE),
    re.compile(r"\n_{3,}\s*\n"),
    re.compile(r"\n>{1,}\s"),
)

_SUBJECT_PREFIX = re.compile(r"^Re:\s*", re.IGNORECASE)


def strip_quoted_reply_body(text: str) -> str:
    """Keep only the prospect's new reply, not the quoted outbound email below it."""
    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return cleaned

    for pattern in _QUOTE_SPLIT_PATTERNS:
        parts = pattern.split(cleaned, maxsplit=1)
        if len(parts) > 1 and parts[0].strip():
            cleaned = parts[0].strip()
            break

    lines: list[str] = []
    for line in cleaned.split("\n"):
        stripped = line.strip()
        if stripped.startswith(">"):
            break
        if stripped:
            lines.append(stripped)
        elif lines:
            break

    if lines:
        return " ".join(lines)

    return cleaned.split("\n", 1)[0].strip()


def normalize_prospect_reply(
    text: str,
    *,
    subject: str | None = None,
) -> str:
    """Strip quoted thread content from the prospect's reply body."""
    body = strip_quoted_reply_body(text)
    if not body:
        return ""

    # Guard against subject-only payloads mistakenly passed as body.
    if subject and body.strip().lower() == subject.strip().lower():
        return ""

    if _SUBJECT_PREFIX.match(body) and "\n" not in body and len(body) < 200:
        return ""

    return body
