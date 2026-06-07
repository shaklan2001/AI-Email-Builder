"""Campaign revision detection and stale artifact invalidation."""

from __future__ import annotations

import hashlib
import json
import re

from app.schemas.campaign import CampaignData

# Phrases that indicate the user is correcting or replacing prior information.
_REVISION_PHRASES: tuple[str, ...] = (
    "change ",
    "update ",
    "edit ",
    "actually ",
    "instead ",
    "that's wrong",
    "that is wrong",
    "thats wrong",
    "no, use",
    "no use ",
    "replace ",
    "not my landing",
    "landing page is not",
    "wrong ",
    "switch to ",
    "new campaign",
    "different product",
    "forget the ",
    "ignore the ",
    "set the ",
    "set my ",
    "make it ",
    "call it ",
    "rename ",
    "remove ",
    "clear ",
    "delete ",
    "drop ",
)

# Explicit field assignments — user is setting a value even without "change"/"update".
_EXPLICIT_FIELD_ASSIGNMENT = re.compile(
    r"\b(?:"
    r"product(?:\s+name)?|service(?:\s+name)?|"
    r"campag(?:n|io|o)n(?:\s+name)?|campaign(?:\s+name)?|"
    r"audience|tone|cta|goal|business\s+goal|"
    r"landing\s+page|website|image(?:\s+url)?|product\s+image"
    r")\s+(?:is|as|to|=)\s+",
    re.IGNORECASE,
)

_PIVOT_PHRASES: tuple[str, ...] = (
    "instead of",
    "switch to",
    "new campaign",
    "not airpure",
    "not air pure",
    "t-shirt",
    "tshirt",
    "tee campaign",
)

_CAMPAIGN_STATE_FIELDS: tuple[str, ...] = (
    "campaign_name",
    "product_info",
    "audience",
    "business_goal",
    "tone",
    "cta",
    "landing_page",
    "product_image",
)


def is_explicit_field_update(text: str) -> bool:
    """True when the user names a field and assigns a new value in plain language."""
    cleaned = text.strip()
    if not cleaned:
        return False
    return bool(_EXPLICIT_FIELD_ASSIGNMENT.search(cleaned))


def should_overwrite_campaign_fields(
    text: str,
    *,
    brief_status: str | None = None,
) -> bool:
    """True when user intent should replace existing campaign field values."""
    if brief_status == "editing":
        return True
    if brief_status == "pending_approval" and (
        is_revision_message(text) or is_explicit_field_update(text)
    ):
        return True
    return is_revision_message(text) or is_explicit_field_update(text)


def is_revision_message(text: str) -> bool:
    lower = text.lower().strip()
    if not lower:
        return False
    return (
        any(phrase in lower for phrase in _REVISION_PHRASES)
        or any(phrase in lower for phrase in _PIVOT_PHRASES)
        or is_explicit_field_update(text)
    )


def campaign_snapshot(campaign: CampaignData) -> str:
    payload = {field: getattr(campaign, field) or "" for field in _CAMPAIGN_STATE_FIELDS}
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def campaign_changed(before: CampaignData, after: CampaignData) -> bool:
    return campaign_snapshot(before) != campaign_snapshot(after)


def is_material_change(before: CampaignData, after: CampaignData) -> bool:
    """True when product, name, goal, or audience changed — workflow must regenerate."""
    keys = ("campaign_name", "product_info", "business_goal", "audience", "cta", "tone")
    for key in keys:
        if (getattr(before, key) or "").strip() != (getattr(after, key) or "").strip():
            return True
    return False


def stale_artifact_reset(*, clear_brief: bool = True) -> dict[str, object]:
    """Drop generated artifacts so the latest campaign fields are the only source of truth."""
    from app.schemas.conversation_stage import ConversationStage

    reset: dict[str, object] = {
        "workflow": None,
        "email_templates": [],
        "brief_approved": False,
        "review_status": None,
        "regenerate_workflow": False,
        "current_stage": ConversationStage.DISCOVERY,
    }
    if clear_brief:
        reset["campaign_brief"] = None
        reset["brief_status"] = None
    return reset
