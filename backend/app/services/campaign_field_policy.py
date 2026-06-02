"""Required vs optional campaign fields, skip detection, and defaults."""

from __future__ import annotations

import re

from app.schemas.campaign import CampaignData

REQUIRED_FIELD = "product_info"

OPTIONAL_FIELDS: tuple[str, ...] = (
    "business_goal",
    "audience",
    "tone",
    "cta",
    "landing_page",
    "product_image",
)

FIELD_DEFAULTS: dict[str, str] = {
    "business_goal": "Product Promotion",
    "audience": "General Customers",
    "tone": "Professional",
    "cta": "Learn More",
}

FIELD_LABELS: dict[str, str] = {
    "product_info": "Product / Service",
    "business_goal": "Business Goal",
    "audience": "Target Audience",
    "tone": "Tone",
    "cta": "CTA",
    "landing_page": "Landing Page",
    "product_image": "Images",
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
    return any(phrase in normalized for phrase in ("don't know", "not sure", "no preference"))


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


def next_field_to_collect(
    campaign: CampaignData,
    skipped_fields: set[str],
    *,
    include_optional: bool = False,
) -> str | None:
    if not _field_value(campaign, REQUIRED_FIELD):
        return REQUIRED_FIELD

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
        label = FIELD_LABELS.get(field, field)
        if value:
            lines.append(f"- {label}: {value}")
    return lines


def used_defaults(campaign: CampaignData, skipped_fields: set[str]) -> bool:
    for field in OPTIONAL_FIELDS:
        if field in skipped_fields:
            return True
        if not _field_value(campaign, field):
            return True
    return False
