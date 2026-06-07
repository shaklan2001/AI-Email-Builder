"""Required vs optional campaign fields, skip detection, and defaults."""

from __future__ import annotations

import re

from app.schemas.campaign import CampaignData
from app.schemas.follow_up_delay import FollowUpDelay

REQUIRED_FIELD = "product_info"
EMAIL_LENGTH_FIELD = "email_length"
WANTS_FOLLOW_UP_FIELD = "wants_follow_up"
WANTS_CTA_FIELD = "wants_cta"
CTA_LABEL_FIELD = "cta"
FOLLOW_UP_DELAY_FIELD = "follow_up_delay"
DEFAULT_FOLLOW_UP_DELAY = FollowUpDelay(value=3, unit="days")

CTA_URL_FIELD = "landing_page"

# Collected (or explicitly skipped) before showing the campaign brief.
BRIEF_COLLECTION_FIELDS: tuple[str, ...] = (
    "campaign_name",
    "audience",
)

_CTA_LINK_INTENT_PHRASES: tuple[str, ...] = (
    "cta url",
    "cta link",
    "button link",
    "link for the cta",
    "link for cta",
    "link to my",
    "link to our",
    "link to the",
    "link to your",
    "link to a",
    "link to company",
    "link to website",
    "company website",
    "my website",
    "our website",
    "with a link",
    "with link",
    "needs a url",
    "need a url",
    "needs a link",
    "need a link",
)

_NO_CTA_PHRASES: tuple[str, ...] = (
    "no button",
    "no cta",
    "no call to action",
    "no call-to-action",
    "without button",
    "without cta",
    "without a button",
    "don't want a button",
    "dont want a button",
    "do not want a button",
    "don't need a button",
    "dont need a button",
)

_YES_CTA_PHRASES: tuple[str, ...] = (
    "yes",
    "yeah",
    "yep",
    "yup",
    "sure",
    "please",
    "definitely",
    "absolutely",
    "of course",
    "i do",
    "i want",
    "sounds good",
)

_KNOWN_CTA_LABELS: tuple[tuple[str, str], ...] = (
    ("learn more", "Learn More"),
    ("shop now", "Shop Now"),
    ("book a free demo", "Book a Free Demo"),
    ("book a demo", "Book a Demo"),
    ("book demo", "Book a Demo"),
    ("book a call", "Book a Call"),
    ("book the call", "Book a Call"),
    ("book call", "Book a Call"),
    ("schedule a call", "Book a Call"),
    ("get started", "Get Started"),
    ("contact us", "Contact Us"),
    ("sign up", "Sign Up"),
)

_CTA_INFER_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bbook(?:s|ing)?\s+(?:the\s+|a\s+)?call\b", re.IGNORECASE), "Book a Call"),
    (re.compile(r"\bschedule\s+(?:a\s+)?call\b", re.IGNORECASE), "Book a Call"),
    (re.compile(r"\bbook\s+(?:a\s+)?(?:free\s+)?demo\b", re.IGNORECASE), "Book a Demo"),
    (re.compile(r"\bshop\s+now\b", re.IGNORECASE), "Shop Now"),
    (re.compile(r"\bget\s+started\b", re.IGNORECASE), "Get Started"),
    (re.compile(r"\bcontact\s+us\b", re.IGNORECASE), "Contact Us"),
    (re.compile(r"\blearn\s+more\b", re.IGNORECASE), "Learn More"),
)

_CTA_LABEL_CAPTURE = re.compile(
    r"(?:cta|button|call[- ]to[- ]action)\s*"
    r"(?:is|should\s+be|named|called|say[s]?|that|:)\s*[\"']?(.+?)[\"']?\s*$",
    re.IGNORECASE,
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
    "landing_page": "CTA URL",
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
    "decide yourself",
    "decide your self",
    "you can decide",
    "can decide",
    "decide for me",
    "decide on your own",
    "let you decide",
)

_DELEGATE_REGEXES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\bdecide\s+(?:it\s+)?(?:yourself|your\s+self|for\s+me|on\s+your\s+own)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\byou\s+can\s+decide\b", re.IGNORECASE),
    re.compile(r"\blet\s+(?:you|me)\s+decide\b", re.IGNORECASE),
)

_ACKNOWLEDGEMENT_PHRASES: tuple[str, ...] = (
    "ok",
    "okay",
    "oky",
    "k",
    "cool",
    "thanks",
    "thank you",
    "thik hai",
    "theek hai",
    "got it",
    "fine",
    "np",
    "no problem",
    "sure thing",
    "sounds good",
    "alright",
    "all right",
    "done",
    "great",
    "nice",
    "perfect",
)

_PROCEED_PHRASES: tuple[str, ...] = (
    "looks good",
    "look good",
    "looks cool",
    "look cool",
    "everything look good",
    "everything looks good",
    "everything look cool",
    "everything looks cool",
    "everything's good",
    "everythings good",
    "all set",
    "we're good",
    "were good",
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
    "don't ask again",
    "dont ask again",
    "stop asking",
    "no more questions",
    "that's all",
    "thats all",
    "just build it",
    "build it",
    "lock it",
    "lock this",
    "lock the brief",
    "finalize",
    "finalize it",
    "that fine",
    "that's fine",
    "thats fine",
)

_DECLINING_TWEAKS_EXACT = frozenset({"no", "nope", "nah"})

_VAGUE_PRODUCT_PHRASES: frozenset[str] = frozenset(
    {
        "new product",
        "my product",
        "a product",
        "the product",
        "new service",
        "my service",
        "a service",
        "the service",
        "new item",
        "my item",
        "a item",
        "the item",
        "product",
        "service",
        "something",
        "stuff",
        "email",
        "campaign",
    },
)

_VAGUE_PRODUCT_PATTERN = re.compile(
    r"^(?:my|a|an|the|new)\s+(?:new\s+)?(?:product|service|item|thing)s?$",
    re.IGNORECASE,
)


def is_vague_product_info(value: str | None) -> bool:
    """True when the value is a generic placeholder, not a real product name."""
    if not value or not str(value).strip():
        return True
    normalized = re.sub(r"\s+", " ", str(value).strip().lower())
    if normalized in _VAGUE_PRODUCT_PHRASES:
        return True
    if _VAGUE_PRODUCT_PATTERN.fullmatch(normalized):
        return True
    return False


_PRODUCT_INTENT_TAIL = re.compile(
    r"\s+and\s+(?:i\s+)?(?:want|wants|need|would like)\s+to\s+.+$",
    re.IGNORECASE,
)
_CONVERSATIONAL_PREFIX = re.compile(
    r"^(?:so\s+)?(?:basically\s+)?(?:my\s+product\s+is\s+)?",
    re.IGNORECASE,
)
_RUN_BUSINESS = re.compile(
    r"^(?:that\s+)?(?:i\s+)?(?:run|have|own|operate)\s+a\s+(.+)$",
    re.IGNORECASE,
)
_BUSINESS_SUFFIX = re.compile(
    r"\s+(?:components?|componet|compan(?:y|ies)|services?|agenc(?:y|ies)|firm|business|studio|shop|store)s?$",
    re.IGNORECASE,
)


def condense_product_info(value: str | None) -> str | None:
    """Turn a narrative business description into a short product/service label."""
    if not value or not str(value).strip():
        return None

    text = re.sub(r"\s+", " ", str(value).strip())
    text = _PRODUCT_INTENT_TAIL.sub("", text).strip()
    text = _CONVERSATIONAL_PREFIX.sub("", text).strip()

    run_match = _RUN_BUSINESS.match(text)
    if run_match:
        text = _BUSINESS_SUFFIX.sub("", run_match.group(1).strip()).strip()
        if text == text.lower() and len(text.split()) <= 8:
            return text.title()

    if len(text) > 60:
        text = re.split(r"\s+and\s+", text, maxsplit=1, flags=re.IGNORECASE)[0].strip()

    if not text or is_vague_product_info(text):
        return None

    return text


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


def is_delegate_message(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    if any(phrase in normalized for phrase in _DELEGATE_PHRASES):
        return True
    return any(pattern.search(normalized) for pattern in _DELEGATE_REGEXES)


def is_acknowledgement_message(text: str) -> bool:
    normalized = text.strip().lower().rstrip(".!")
    if not normalized:
        return False
    if normalized in _ACKNOWLEDGEMENT_PHRASES:
        return True
    return any(phrase in normalized for phrase in _ACKNOWLEDGEMENT_PHRASES)


def is_skip_message(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    if is_delegate_message(text):
        return True
    if is_acknowledgement_message(text):
        return True
    if normalized in _SKIP_PHRASES:
        return True
    if any(normalized.startswith(f"{phrase} ") for phrase in _SKIP_PHRASES):
        return True
    if any(normalized.endswith(f" {phrase}") for phrase in _SKIP_PHRASES):
        return True
    return any(phrase in normalized for phrase in ("don't know", "not sure", "no preference"))


def is_hard_skip_message(text: str) -> bool:
    """Skip/opt-out without delegating the decision to the AI."""
    if is_delegate_message(text) or is_acknowledgement_message(text):
        return False
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


def should_default_preference_field(text: str, field: str) -> bool:
    """True when the user wants the AI to pick or is acking during preference collection."""
    if field not in (
        EMAIL_LENGTH_FIELD,
        WANTS_FOLLOW_UP_FIELD,
        WANTS_CTA_FIELD,
        CTA_LABEL_FIELD,
        FOLLOW_UP_DELAY_FIELD,
    ):
        return is_skip_message(text)
    return (
        is_delegate_message(text)
        or is_acknowledgement_message(text)
        or is_hard_skip_message(text)
        or is_proceed_message(text)
    )


def is_no_cta_message(text: str) -> bool:
    """True when the user explicitly declines a CTA button."""
    normalized = text.strip().lower().rstrip(".!")
    if not normalized:
        return False
    if normalized in ("no", "nope", "nah"):
        return True
    return any(phrase in normalized for phrase in _NO_CTA_PHRASES)


def _canonical_cta_label(text: str) -> str | None:
    lower = text.strip().lower().rstrip(".!")
    if not lower:
        return None
    for phrase, label in _KNOWN_CTA_LABELS:
        if lower == phrase or phrase in lower:
            return label
    return None


def infer_cta_label_from_message(
    text: str,
    *,
    campaign: CampaignData | None = None,
) -> str | None:
    """Infer a CTA label from natural language (e.g. 'book the call' → Book a Call)."""
    cleaned = text.strip()
    if not cleaned or is_no_cta_message(cleaned):
        return None

    canonical = _canonical_cta_label(cleaned)
    if canonical:
        return canonical

    for pattern, label in _CTA_INFER_PATTERNS:
        if pattern.search(cleaned):
            return label

    capture = _CTA_LABEL_CAPTURE.search(cleaned)
    if capture:
        raw = capture.group(1).strip().rstrip(".\"'")
        if raw and len(raw) <= 60:
            return raw.title() if raw.islower() else raw

    lower = cleaned.lower()
    if "book" in lower and "call" in lower:
        return "Book a Call"
    if campaign is not None and "demo" in lower and "book" in lower:
        return "Book a Demo"

    return None


def parse_cta_label(text: str) -> str | None:
    """Parse an explicit CTA button label. Bare yes/no are not labels."""
    if is_no_cta_message(text):
        return None

    cleaned = text.strip()
    if not cleaned:
        return None

    inferred = infer_cta_label_from_message(cleaned)
    if inferred:
        return inferred

    lower = cleaned.lower().rstrip(".!")
    if lower in _YES_CTA_PHRASES or is_acknowledgement_message(text):
        return None

    if is_delegate_message(text):
        return FIELD_DEFAULTS["cta"]

    words = cleaned.split()
    if 1 <= len(words) <= 6 and len(cleaned) <= 50 and not is_skip_message(text):
        return cleaned.title() if cleaned.islower() else cleaned

    return None


def has_cta_content(campaign: CampaignData) -> bool:
    """True when a CTA label or destination URL is already known."""
    return bool(_field_value(campaign, "cta") or _field_value(campaign, "landing_page"))


def infer_wants_cta_from_campaign(
    campaign: CampaignData,
    messages: list[dict[str, str]] | None = None,
    *,
    wants_cta: object = None,
) -> bool | None:
    """Infer CTA preference from collected fields when the user skipped an explicit yes/no."""
    if has_wants_cta(wants_cta):
        return bool(wants_cta)
    if has_cta_content(campaign):
        return True
    for message in reversed(messages or []):
        if message.get("role") != "user":
            continue
        text = message.get("content", "").strip().lower()
        if not text:
            continue
        if any(phrase in text for phrase in _CTA_LINK_INTENT_PHRASES):
            return True
        if infer_cta_label_from_message(text, campaign=campaign) is not None:
            return True
    return None


def is_declining_tweaks_message(text: str) -> bool:
    """Bare no/nope when declining optional tweaks — not declining a CTA button."""
    normalized = text.strip().lower().rstrip(".!")
    return normalized in _DECLINING_TWEAKS_EXACT


def parse_wants_cta(text: str, *, campaign: CampaignData | None = None) -> bool | None:
    """Parse whether the user wants a CTA button."""
    if campaign is not None and has_cta_content(campaign):
        return True

    if is_no_cta_message(text):
        return False

    if infer_cta_label_from_message(text, campaign=campaign) is not None or parse_cta_label(text) is not None:
        return True

    cleaned = text.strip().lower().rstrip(".!")
    if not cleaned:
        return None

    if any(phrase in cleaned for phrase in _CTA_LINK_INTENT_PHRASES):
        return True

    if cleaned in _YES_CTA_PHRASES or any(
        cleaned == phrase or cleaned.startswith(f"{phrase} ")
        for phrase in _YES_CTA_PHRASES
    ):
        return True

    if is_acknowledgement_message(text):
        return True

    return None


def has_wants_cta(wants_cta: object) -> bool:
    return isinstance(wants_cta, bool)


def is_proceed_message(text: str) -> bool:
    normalized = text.strip().lower().rstrip(".!")
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
            if 2 <= len(product) <= 80 and not is_vague_product_info(product):
                return product.title() if product.islower() else product

    words = cleaned.split()
    if 1 <= len(words) <= 4 and not any(w.lower() in ("the", "a", "an", "my", "for") for w in words[:1]):
        if len(cleaned) >= 3 and not is_vague_product_info(cleaned):
            return cleaned.title() if cleaned.islower() else cleaned

    return None


def resolve_wants_cta(wants_cta: object, skipped_fields: set[str] | None = None) -> bool | None:
    """Effective CTA preference from state flags and skipped fields."""
    if isinstance(wants_cta, bool):
        return wants_cta
    skipped = skipped_fields or set()
    if WANTS_CTA_FIELD in skipped or CTA_LABEL_FIELD in skipped:
        return False
    return None


def apply_field_defaults(
    campaign: CampaignData,
    skipped_fields: set[str] | None = None,
    *,
    wants_cta: object = None,
) -> CampaignData:
    """Fill empty optional fields with defaults (skipped or missing)."""
    data = campaign.model_dump()
    skipped = skipped_fields or set()
    effective_wants_cta = resolve_wants_cta(wants_cta, skipped)

    if effective_wants_cta is False:
        data["cta"] = None
        data["landing_page"] = None

    for field in OPTIONAL_FIELDS:
        if field == "cta":
            if effective_wants_cta is False:
                continue
            if _field_value(campaign, "cta"):
                continue
            if effective_wants_cta is True and "cta" in FIELD_DEFAULTS:
                data["cta"] = FIELD_DEFAULTS["cta"]
            continue
        if field == "landing_page" and effective_wants_cta is False:
            continue
        if _field_value(campaign, field):
            continue
        if field in FIELD_DEFAULTS:
            data[field] = FIELD_DEFAULTS[field]

    for field in skipped:
        if field in FIELD_DEFAULTS and not data.get(field):
            if field == "cta":
                if effective_wants_cta is False:
                    continue
                if effective_wants_cta is True:
                    data[field] = FIELD_DEFAULTS[field]
                continue
            if field == "landing_page" and effective_wants_cta is False:
                continue
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


def user_wants_cta_url(
    campaign: CampaignData,
    messages: list[dict[str, str]] | None = None,
    *,
    wants_cta: object = None,
) -> bool:
    """True when a CTA button is in use and needs a destination URL."""
    if wants_cta is not True:
        return False
    if _field_value(campaign, "cta"):
        return True

    for message in reversed(messages or []):
        if message.get("role") != "user":
            continue
        text = message.get("content", "").strip().lower()
        if not text:
            continue
        if any(phrase in text for phrase in _CTA_LINK_INTENT_PHRASES):
            return True
        if re.search(r"\b(?:book(?:\s+a)?\s+demo|shop\s+now|sign\s+up|get\s+started|contact\s+us)\b", text):
            return True
    return False


def next_field_to_collect(
    campaign: CampaignData,
    skipped_fields: set[str],
    *,
    include_optional: bool = False,
    follow_up_delay: object = None,
    wants_follow_up: object = None,
    wants_cta: object = None,
    email_length: object = None,
    messages: list[dict[str, str]] | None = None,
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

    if not has_wants_cta(wants_cta) and WANTS_CTA_FIELD not in skipped_fields:
        return WANTS_CTA_FIELD

    if wants_cta is True:
        if CTA_LABEL_FIELD not in skipped_fields and not _field_value(campaign, CTA_LABEL_FIELD):
            return CTA_LABEL_FIELD

    if (
        wants_cta is True
        and user_wants_cta_url(campaign, messages, wants_cta=wants_cta)
        and CTA_URL_FIELD not in skipped_fields
        and not _field_value(campaign, CTA_URL_FIELD)
    ):
        return CTA_URL_FIELD

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
    *,
    latest_message: str | None = None,
) -> tuple[set[str], dict[str, str]]:
    """Mark field skipped and return default value updates when applicable."""
    updated = set(skipped_fields)
    updated.add(field)
    patches: dict[str, str] = {}
    if field == CTA_LABEL_FIELD and latest_message is not None:
        if is_delegate_message(latest_message):
            patches["cta"] = FIELD_DEFAULTS["cta"]
        elif is_no_cta_message(latest_message) or is_hard_skip_message(latest_message):
            return updated, patches
        return updated, patches
    if field in FIELD_DEFAULTS:
        patches[field] = FIELD_DEFAULTS[field]
    return updated, patches


def mark_all_optional_skipped(skipped_fields: set[str]) -> set[str]:
    return skipped_fields | set(OPTIONAL_FIELDS) | {WANTS_CTA_FIELD, CTA_LABEL_FIELD}


def preference_default_updates(
    field: str,
    *,
    delegate: bool = False,
) -> tuple[dict[str, object], dict[str, object], set[str]]:
    """Return (prefs_updates, delay_updates, skipped_additions) for a preference field."""
    from app.services.collection_preferences import default_email_length

    prefs: dict[str, object] = {}
    delay: dict[str, object] = {}
    skipped = {field}

    if field == EMAIL_LENGTH_FIELD:
        prefs["email_length"] = default_email_length()
    elif field == WANTS_FOLLOW_UP_FIELD:
        if delegate:
            prefs["wants_follow_up"] = True
        else:
            prefs["wants_follow_up"] = False
            prefs["follow_up_delay"] = None
    elif field == WANTS_CTA_FIELD:
        if delegate:
            prefs["wants_cta"] = True
        else:
            prefs["wants_cta"] = False
    elif field == CTA_LABEL_FIELD:
        if delegate:
            prefs["cta"] = FIELD_DEFAULTS["cta"]
    elif field == FOLLOW_UP_DELAY_FIELD:
        delay["follow_up_delay"] = DEFAULT_FOLLOW_UP_DELAY.to_api_dict()

    return prefs, delay, skipped


def fill_missing_preference_defaults(
    *,
    email_length: object = None,
    wants_follow_up: object = None,
    wants_cta: object = None,
    follow_up_delay: object = None,
    delegate: bool = True,
) -> tuple[dict[str, object], dict[str, object], set[str]]:
    """Apply defaults for any unset preference fields (e.g. user said proceed)."""
    prefs: dict[str, object] = {}
    delay: dict[str, object] = {}
    skipped: set[str] = set()

    if not has_email_length(email_length):
        p, d, s = preference_default_updates(EMAIL_LENGTH_FIELD, delegate=delegate)
        prefs.update(p)
        delay.update(d)
        skipped |= s

    if not has_wants_follow_up(wants_follow_up):
        p, d, s = preference_default_updates(
            WANTS_FOLLOW_UP_FIELD,
            delegate=delegate,
        )
        prefs.update(p)
        delay.update(d)
        skipped |= s
        wants_follow_up = prefs.get("wants_follow_up", wants_follow_up)

    effective_wants = prefs.get("wants_follow_up", wants_follow_up)
    if (
        follow_up_delay_required(wants_follow_up=effective_wants)
        and not has_follow_up_delay(follow_up_delay)
        and not has_follow_up_delay(delay.get("follow_up_delay"))
    ):
        p, d, s = preference_default_updates(FOLLOW_UP_DELAY_FIELD, delegate=delegate)
        prefs.update(p)
        delay.update(d)
        skipped |= s

    if not has_wants_cta(wants_cta) and WANTS_CTA_FIELD not in skipped:
        p, d, s = preference_default_updates(WANTS_CTA_FIELD, delegate=delegate)
        prefs.update(p)
        delay.update(d)
        skipped |= s
        wants_cta = prefs.get("wants_cta", wants_cta)

    if prefs.get("wants_cta", wants_cta) is True and CTA_LABEL_FIELD not in skipped:
        p, d, s = preference_default_updates(CTA_LABEL_FIELD, delegate=True)
        prefs.update(p)
        delay.update(d)
        skipped |= s

    return prefs, delay, skipped


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
    wants_cta = conv_state.get("wants_cta")
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

    raw_messages = conv_state.get("messages")
    messages = raw_messages if isinstance(raw_messages, list) else None
    next_field = next_field_to_collect(
        campaign,
        skipped,
        include_optional=conv_state.get("brief_status") == "editing",
        follow_up_delay=parsed_delay,
        wants_follow_up=wants_follow_up,
        wants_cta=wants_cta,
        email_length=email_length,
        messages=messages,
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
