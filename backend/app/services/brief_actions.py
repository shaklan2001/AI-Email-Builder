"""User actions on the campaign brief (spec 15.2)."""

from typing import Literal

BriefUserAction = Literal["approve", "edit"]


def parse_brief_user_action(message: str) -> BriefUserAction | None:
    normalized = message.strip().lower().rstrip(".!")
    if normalized in {"looks good", "looks good to me"}:
        return "approve"
    if normalized in {
        "edit campaign details",
        "edit campaign detail",
        "edit details",
    }:
        return "edit"
    return None
