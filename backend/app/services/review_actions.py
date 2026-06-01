"""User actions on the workflow review stage."""

from typing import Literal

ReviewUserAction = Literal["approve", "edit_campaign", "regenerate_workflow"]

_LOOKS_GOOD = frozenset({"looks good", "looks good to me", "approve workflow"})
_EDIT_CAMPAIGN = frozenset(
    {
        "edit campaign",
        "edit campaign details",
        "edit campaign detail",
        "edit details",
    },
)
_REGENERATE = frozenset(
    {
        "regenerate workflow",
        "regenerate",
        "rebuild workflow",
        "redo workflow",
    },
)


def parse_review_user_action(message: str) -> ReviewUserAction | None:
    normalized = message.strip().lower().rstrip(".!")
    if normalized in _LOOKS_GOOD:
        return "approve"
    if normalized in _EDIT_CAMPAIGN:
        return "edit_campaign"
    if normalized in _REGENERATE:
        return "regenerate_workflow"
    return None
