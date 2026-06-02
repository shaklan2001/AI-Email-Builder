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


def is_revision_message(text: str) -> bool:
    lower = text.lower().strip()
    if not lower:
        return False
    return any(phrase in lower for phrase in _REVISION_PHRASES) or any(
        phrase in lower for phrase in _PIVOT_PHRASES
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
    """Drop generated workflow and approval so the latest brief is the only source of truth."""
    reset: dict[str, object] = {
        "workflow": None,
        "brief_approved": False,
    }
    if clear_brief:
        reset["campaign_brief"] = None
        reset["brief_status"] = None
    return reset
