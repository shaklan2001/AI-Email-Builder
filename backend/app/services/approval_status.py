"""Unified approval_status derived from brief + review flags."""

from __future__ import annotations

from enum import StrEnum

from app.langgraph.state import ConversationState
from app.services.conversation_stage import _has_workflow_steps


class ApprovalStatus(StrEnum):
    COLLECTING = "collecting"
    BRIEF_PENDING = "brief_pending"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    ACTIVE = "active"


def resolve_approval_status(state: ConversationState) -> str:
    """Map legacy brief/review fields to a single approval_status."""
    if state.get("review_status") == "approved":
        return ApprovalStatus.APPROVED.value

    brief_status = state.get("brief_status")
    if brief_status == "pending_approval":
        return ApprovalStatus.BRIEF_PENDING.value

    if brief_status == "editing":
        return ApprovalStatus.COLLECTING.value

    workflow = state.get("workflow")
    if _has_workflow_steps(workflow):
        review_status = state.get("review_status")
        if review_status in (None, "pending", "editing"):
            return ApprovalStatus.REVIEW_PENDING.value
        if review_status == "approved":
            return ApprovalStatus.APPROVED.value

    if state.get("brief_approved") and not _has_workflow_steps(workflow):
        return ApprovalStatus.BRIEF_PENDING.value

    return ApprovalStatus.COLLECTING.value


def sync_approval_fields(state: ConversationState) -> None:
    """Write approval_status and keep legacy fields consistent."""
    status = resolve_approval_status(state)
    state["approval_status"] = status

    if status == ApprovalStatus.APPROVED.value:
        state["review_status"] = "approved"
        state["brief_approved"] = True
        if state.get("brief_status") is None:
            state["brief_status"] = "approved"
