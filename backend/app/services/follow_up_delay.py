"""Parse, format, and apply configurable follow-up wait timing."""

from __future__ import annotations

import re
from datetime import timedelta

from app.schemas.follow_up_delay import FollowUpDelay, FollowUpDelayUnit
from app.schemas.workflow import WorkflowDefinition

FOLLOW_UP_DELAY_QUESTION = (
    "If a recipient does not reply, when should I send the follow-up?\n\n"
    "Examples: 2 Minutes, 4 Hours, 1 Day, 3 Days, 2 Weeks"
)

_DELAY_PATTERNS: tuple[tuple[re.Pattern[str], FollowUpDelayUnit], ...] = (
    (re.compile(r"(\d+)[\s-]*(?:mins?|minutes?)\b", re.IGNORECASE), "minutes"),
    (re.compile(r"(\d+)[\s-]*hours?\b", re.IGNORECASE), "hours"),
    (re.compile(r"(\d+)[\s-]*days?\b", re.IGNORECASE), "days"),
    (re.compile(r"(\d+)[\s-]*weeks?\b", re.IGNORECASE), "weeks"),
)

_AFFIRMATION_PHRASES: tuple[str, ...] = (
    "yes",
    "yeah",
    "yep",
    "yup",
    "sure",
    "ok",
    "okay",
    "sounds good",
    "looks good",
    "look good",
    "look cool",
    "looks cool",
    "looks great",
    "love it",
    "love them",
    "like it",
    "like them",
    "perfect",
    "great",
    "nice",
    "good",
    "keep it",
    "keep the",
    "that's fine",
    "thats fine",
    "works for me",
    "fine with me",
)


def parse_follow_up_delay(text: str) -> FollowUpDelay | None:
    cleaned = text.strip()
    if not cleaned:
        return None
    for pattern, unit in _DELAY_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            value = int(match.group(1))
            if value >= 1:
                return FollowUpDelay(value=value, unit=unit)
    return None


def is_affirmation_message(text: str) -> bool:
    """True when the user approves or agrees without giving a new value."""
    normalized = text.strip().lower()
    if not normalized:
        return False
    if parse_follow_up_delay(text) is not None:
        return False
    return any(phrase in normalized for phrase in _AFFIRMATION_PHRASES)


def infer_follow_up_delay_from_messages(
    messages: list[dict[str, str]],
) -> FollowUpDelay | None:
    """Find the most recent delay mentioned in user or assistant messages."""
    for message in reversed(messages):
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            continue
        parsed = parse_follow_up_delay(content)
        if parsed is not None:
            return parsed
    return None


def follow_up_delay_from_state(raw: object) -> FollowUpDelay | None:
    if isinstance(raw, FollowUpDelay):
        return raw
    if not isinstance(raw, dict):
        return None
    try:
        return FollowUpDelay.model_validate(raw)
    except Exception:
        return None


def format_wait_label(delay: FollowUpDelay) -> str:
    unit_word = delay.unit.rstrip("s")
    if delay.value != 1:
        unit_word = delay.unit
    label = unit_word.capitalize()
    if delay.value == 1 and delay.unit == "days":
        label = "Day"
    elif delay.value == 1 and delay.unit == "weeks":
        label = "Week"
    elif delay.value == 1 and delay.unit == "hours":
        label = "Hour"
    elif delay.value == 1 and delay.unit == "minutes":
        label = "Minute"
    return f"Wait {delay.value} {label}"


def format_follow_up_strategy(delay: FollowUpDelay) -> str:
    return f"{format_wait_label(delay)}\nSend Follow-Up If No Reply"


def format_follow_up_delay_brief(delay: FollowUpDelay) -> str:
    """Human-readable delay for the campaign brief (e.g. ``3 Days``)."""
    unit_labels: dict[FollowUpDelayUnit, tuple[str, str]] = {
        "minutes": ("Minute", "Minutes"),
        "hours": ("Hour", "Hours"),
        "days": ("Day", "Days"),
        "weeks": ("Week", "Weeks"),
    }
    singular, plural = unit_labels[delay.unit]
    unit_word = singular if delay.value == 1 else plural
    return f"{delay.value} {unit_word}"


def follow_up_delay_to_timedelta(delay: FollowUpDelay) -> timedelta:
    if delay.unit == "minutes":
        return timedelta(minutes=delay.value)
    if delay.unit == "hours":
        return timedelta(hours=delay.value)
    if delay.unit == "weeks":
        return timedelta(weeks=delay.value)
    return timedelta(days=delay.value)


def wait_days_for_workflow_step(delay: FollowUpDelay) -> int:
    """Legacy `days` field on wait steps (minimum 1 day for sub-day waits)."""
    if delay.unit == "days":
        return delay.value
    if delay.unit == "weeks":
        return delay.value * 7
    if delay.unit == "minutes":
        return max(1, delay.value // (24 * 60))
    return max(1, (delay.value + 23) // 24)


def apply_follow_up_delay_to_workflow(
    definition: WorkflowDefinition,
    delay: FollowUpDelay,
) -> WorkflowDefinition:
    from app.services.workflow_structure import apply_delay_to_workflow

    return apply_delay_to_workflow(definition, delay)
