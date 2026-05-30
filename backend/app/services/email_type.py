"""Classify workflow email steps for generation (promotional, follow-up, reply)."""

from __future__ import annotations

from typing import Literal

from app.schemas.workflow import WorkflowStep

EmailType = Literal["promotional", "follow_up", "reply"]

_REPLY_HINTS = ("reply", "response", "auto reply", "ai reply")
_FOLLOW_UP_HINTS = ("follow", "follow-up", "follow up", "nudge", "reminder", "no reply", "second touch")


def _step_name_lower(step: WorkflowStep) -> str:
    return (step.name or "").strip().lower()


def _send_email_indices(steps: list[WorkflowStep]) -> list[int]:
    return [i for i, s in enumerate(steps) if s.type == "send_email"]


def workflow_has_reply_branch(steps: list[WorkflowStep]) -> bool:
    return any(s.type in ("reply_condition", "interested_branch", "condition") for s in steps)


def infer_email_type(step: WorkflowStep, steps: list[WorkflowStep]) -> EmailType:
    """Infer email intent from step metadata and position in the workflow."""
    name = _step_name_lower(step)
    if any(hint in name for hint in _REPLY_HINTS):
        return "reply"

    if step.branch == "no" or any(hint in name for hint in _FOLLOW_UP_HINTS):
        return "follow_up"

    position = 0
    for i, candidate in enumerate(steps):
        if candidate.id == step.id:
            position = sum(1 for s in steps[:i] if s.type == "send_email")
            break

    if position >= 1:
        return "follow_up"
    return "promotional"


def email_type_label(email_type: EmailType) -> str:
    labels = {
        "promotional": "Promotional (initial outreach)",
        "follow_up": "Follow-up (no reply yet)",
        "reply": "Reply (interested lead response)",
    }
    return labels[email_type]
