"""Required vs optional campaign fields, skip detection, and defaults."""

from __future__ import annotations

import re

from app.schemas.campaign import CampaignData
from app.schemas.follow_up_delay import FollowUpDelay

REQUIRED_FIELD = "product_info"
EMAIL_LENGTH_FIELD = "email_length"
WANTS_FOLLOW_UP_FIELD = "wants_follow_up"
FOLLOW_UP_DELAY_FIELD = "follow_up_delay"
DEFAULT_FOLLOW_UP_DELAY = FollowUpDelay(value=3, unit="days")

# Collected (or explicitly skipped) before showing the campaign brief.
BRIEF_COLLECTION_FIELDS: tuple[str, ...] = (
    "campaign_name",
    "audience",
    "cta",
    "landing_page",
    "product_image",
)

OPTIONAL_FIELDS: tuple[str, ...] = (
    "campaign_name",
    "business_goal",
    "tone",
    "audience",
    "cta",
    "landing_page",
    "product_image",
    "attachments",
    "competitors",
)

FIELD_DEFAULTS: dict[str, str] = {
    "business_goal": "Product Promotion",
    "audience": "General Customers",
    "tone": "Professional",
    "cta": "Learn More",
}

FIELD_LABELS: dict[str, str] = {
    "campaign_name": "Campaign Name",
    "product_info": "Product / Service",
    "business_goal": "Business Goal",
    "audience": "Target Audience",
    "tone": "Tone",
    "cta": "CTA",
    "landing_page": "Landing Page",
    "product_image": "Images",
    "attachments": "Attachments",
    "competitors": "Competitors",
}

ASSUMPTION_LABELS: dict[str, str] = {
    "business_goal": "Goal",
    "tone": "Tone",
    "audience": "Audience",
    "cta": "CTA",
}

_SKIP_PHRASES: tuple[str, ...] = (
    "skip",
    "none",
    "nothing",
    "don't know",
    "dont know",
    "do not know",
    "not sure",
    "no preference",
    "no pref",
    "doesn't matter",
    "doesnt matter",
    "does not matter",
    "n/a",
    "na",
    "no idea",
    "pass",
    "any",
    "whatever",
)

_DELEGATE_PHRASES: tuple[str, ...] = (
    "recommend for me",
    "recommend something",
    "anything works",
    "anything is fine",
    "whatever works",
    "you choose",
    "you decide",
    "your choice",
    "pick for me",
    "choose for me",
    "use a default",
    "use your best judgment",
    "up to you",
    "surprise me",
)

_PROCEED_PHRASES: tuple[str, ...] = (
    "looks good",
    "look good",
    "that's fine",
    "thats fine",
    "good to go",
    "continue",
    "proceed",
    "go ahead",
    "no thanks",
    "no thank you",
    "no changes",
    "no change",
    "all good",
    "sounds good",
    "perfect",
)

_MINIMAL_PRODUCT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"^(?:i\s+)?(?:have\s+a\s+|run\s+a\s+|start\s+a\s+)?(.+?)\s+business\.?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:selling|promoting|marketing)\s+(.+?)\.?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(.+?)\s+(?:business|brand|company|store|shop)\.?$",
        re.IGNORECASE,
    ),
)


def _field_value(campaign: CampaignData, field: str) -> str | None:
    value = getattr(campaign, field, None)
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def normalize_skipped_fields(raw: object) -> set[str]:
    if not isinstance(raw, (list, tuple, set)):
        return set()
    return {str(item) for item in raw if isinstance(item, str)}


def is_skip_message(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    if normalized in _SKIP_PHRASES:
        return True
    if any(normalized.startswith(f"{phrase} ") for phrase in _SKIP_PHRASES):
        return True
    if any(normalized.endswith(f" {phrase}") for phrase in _SKIP_PHRASES):
        return True
    if any(phrase in normalized for phrase in ("don't know", "not sure", "no preference")):
        return True
    return any(phrase in normalized for phrase in _DELEGATE_PHRASES)


def is_proceed_message(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    return any(phrase in normalized for phrase in _PROCEED_PHRASES)


def infer_product_from_minimal_message(text: str) -> str | None:
    cleaned = text.strip().rstrip(".,;:!?")
    if not cleaned or len(cleaned) > 120:
        return None
    if is_skip_message(cleaned):
        return None

    lower = cleaned.lower()
    if lower in ("hello", "hi", "hey", "thanks", "thank you", "ok", "okay", "yes", "no"):
        return None
    if any(
        token in lower
        for token in (
            "audience",
            "tone",
            "cta",
            "goal",
            "website",
            "http",
            "target",
        )
    ):
        return None

    for pattern in _MINIMAL_PRODUCT_PATTERNS:
        match = pattern.match(cleaned)
        if match:
            product = match.group(1).strip()
            if 2 <= len(product) <= 80:
                return product.title() if product.islower() else product

    words = cleaned.split()
    if 1 <= len(words) <= 4 and not any(w.lower() in ("the", "a", "an", "my", "for") for w in words[:1]):
        if len(cleaned) >= 3:
            return cleaned.title() if cleaned.islower() else cleaned

    return None


def apply_field_defaults(
    campaign: CampaignData,
    skipped_fields: set[str] | None = None,
) -> CampaignData:
    """Fill empty optional fields with defaults (skipped or missing)."""
    data = campaign.model_dump()
    skipped = skipped_fields or set()

    for field in OPTIONAL_FIELDS:
        if _field_value(campaign, field):
            continue
        if field in FIELD_DEFAULTS:
            data[field] = FIELD_DEFAULTS[field]

    for field in skipped:
        if field in FIELD_DEFAULTS and not data.get(field):
            data[field] = FIELD_DEFAULTS[field]

    return CampaignData.model_validate(data)


def missing_required_fields(campaign: CampaignData) -> list[str]:
    if not _field_value(campaign, REQUIRED_FIELD):
        return [REQUIRED_FIELD]
    return []


def has_follow_up_delay(state_follow_up_delay: object) -> bool:
    from app.services.follow_up_delay import follow_up_delay_from_state

    return follow_up_delay_from_state(state_follow_up_delay) is not None


def has_email_length(email_length: object) -> bool:
    return isinstance(email_length, str) and bool(email_length.strip())


def has_wants_follow_up(wants_follow_up: object) -> bool:
    return isinstance(wants_follow_up, bool)


def follow_up_delay_required(*, wants_follow_up: object) -> bool:
    return wants_follow_up is True


def is_ready_for_campaign_brief(
    campaign: CampaignData,
    *,
    follow_up_delay: object = None,
    wants_follow_up: object = None,
    email_length: object = None,
) -> bool:
    if missing_required_fields(campaign):
        return False
    if not has_email_length(email_length):
        return False
    if not has_wants_follow_up(wants_follow_up):
        return False
    if follow_up_delay_required(wants_follow_up=wants_follow_up):
        return has_follow_up_delay(follow_up_delay)
    return True


def next_field_to_collect(
    campaign: CampaignData,
    skipped_fields: set[str],
    *,
    include_optional: bool = False,
    follow_up_delay: object = None,
    wants_follow_up: object = None,
    email_length: object = None,
) -> str | None:
    if not _field_value(campaign, REQUIRED_FIELD):
        return REQUIRED_FIELD

    if not has_email_length(email_length) and EMAIL_LENGTH_FIELD not in skipped_fields:
        return EMAIL_LENGTH_FIELD

    if not has_wants_follow_up(wants_follow_up) and WANTS_FOLLOW_UP_FIELD not in skipped_fields:
        return WANTS_FOLLOW_UP_FIELD

    if (
        follow_up_delay_required(wants_follow_up=wants_follow_up)
        and not has_follow_up_delay(follow_up_delay)
        and FOLLOW_UP_DELAY_FIELD not in skipped_fields
    ):
        return FOLLOW_UP_DELAY_FIELD

    for field in BRIEF_COLLECTION_FIELDS:
        if field in skipped_fields:
            continue
        if not _field_value(campaign, field):
            return field

    if not include_optional:
        return None

    for field in OPTIONAL_FIELDS:
        if field in skipped_fields:
            continue
        if not _field_value(campaign, field):
            return field
    return None


def resolve_skip_for_field(
    field: str,
    skipped_fields: set[str],
) -> tuple[set[str], dict[str, str]]:
    """Mark field skipped and return default value updates when applicable."""
    updated = set(skipped_fields)
    updated.add(field)
    patches: dict[str, str] = {}
    if field in FIELD_DEFAULTS:
        patches[field] = FIELD_DEFAULTS[field]
    return updated, patches


def mark_all_optional_skipped(skipped_fields: set[str]) -> set[str]:
    return skipped_fields | set(OPTIONAL_FIELDS)


def assumption_lines(campaign: CampaignData) -> list[str]:
    resolved = apply_field_defaults(campaign)
    lines: list[str] = []
    for field in ("business_goal", "tone", "cta", "audience"):
        value = _field_value(resolved, field)
        label = ASSUMPTION_LABELS.get(field, FIELD_LABELS.get(field, field))
        if value:
            lines.append(f"- {label}: {value}")
    return lines


def compute_collection_missing_fields(
    state: object,
) -> list[str]:
    """Fields still needed before campaign brief (required + next collection step)."""
    from app.langgraph.state import CampaignState, campaign_data_from_state

    if not isinstance(state, dict):
        return [REQUIRED_FIELD, EMAIL_LENGTH_FIELD, WANTS_FOLLOW_UP_FIELD]

    conv_state: CampaignState = state  # type: ignore[assignment]
    campaign = campaign_data_from_state(conv_state)
    missing = list(missing_required_fields(campaign))
    skipped = normalize_skipped_fields(conv_state.get("skipped_fields"))
    delay = conv_state.get("follow_up_delay")
    from app.services.follow_up_delay import follow_up_delay_from_state

    parsed_delay = follow_up_delay_from_state(delay)
    wants_follow_up = conv_state.get("wants_follow_up")
    email_length = conv_state.get("email_length")

    if not has_email_length(email_length) and EMAIL_LENGTH_FIELD not in skipped:
        missing.append(EMAIL_LENGTH_FIELD)
    if not has_wants_follow_up(wants_follow_up) and WANTS_FOLLOW_UP_FIELD not in skipped:
        missing.append(WANTS_FOLLOW_UP_FIELD)
    if (
        follow_up_delay_required(wants_follow_up=wants_follow_up)
        and not has_follow_up_delay(delay)
        and FOLLOW_UP_DELAY_FIELD not in skipped
    ):
        missing.append(FOLLOW_UP_DELAY_FIELD)

    next_field = next_field_to_collect(
        campaign,
        skipped,
        include_optional=conv_state.get("brief_status") == "editing",
        follow_up_delay=parsed_delay,
        wants_follow_up=wants_follow_up,
        email_length=email_length,
    )
    if next_field and next_field not in missing:
        missing.append(next_field)
    return missing


def used_defaults(campaign: CampaignData, skipped_fields: set[str]) -> bool:
    for field in OPTIONAL_FIELDS:
        if field in skipped_fields:
            return True
        if not _field_value(campaign, field):
            return True
    return False
