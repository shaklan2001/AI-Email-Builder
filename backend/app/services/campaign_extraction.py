"""Rule-based extraction from user messages to complement LLM extraction."""

from __future__ import annotations

import re

from app.schemas.campaign import CampaignData
from app.services.campaign_field_policy import (
    condense_product_info,
    infer_product_from_minimal_message,
    is_vague_product_info,
)
from app.services.campaign_revision import is_explicit_field_update, is_revision_message

_HTTP_URL = re.compile(r"https?://[^\s)>\"']+", re.IGNORECASE)
_DOMAIN = re.compile(
    r"\b(?:https?://)?(?:www\.)?"
    r"([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b",
    re.IGNORECASE,
)
_AGE_RANGE = re.compile(
    r"(?:age[s]?\s*)?(\d{1,2})\s*[-–—to]+\s*(\d{1,2})",
    re.IGNORECASE,
)
_AUDIENCE_PHRASE = re.compile(
    r"target\s+audience\s+(?:is\s+)?(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_OUTREACH_AUDIENCE = re.compile(
    r"(?:send|reach|email)\s+(?:\w+\s+){0,3}to\s+(?:the\s+)?(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_WEBSITE_HINT = re.compile(
    r"(?:my\s+)?(?:website|site|landing\s+page)(?:\s+url)?\s*(?:is\s+|:)?\s*"
    r"((?:https?://)?(?:www\.)?(?:[a-z0-9-]+\.)+[a-z]{2,})",
    re.IGNORECASE,
)
_IMAGE_HINT = re.compile(
    r"(?:product\s+)?image(?:\s+url)?|(?:this\s+)?(?:is\s+)?(?:my\s+)?(?:product\s+)?(?:picture|photo)",
    re.IGNORECASE,
)
_CTA_PHRASE = re.compile(
    r"(?:cta|call[- ]to[- ]action)\s*(?:is\s+|:)?\s*(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_TONE_PHRASE = re.compile(
    r"(?:tone|style)\s*(?:is\s+|:)?\s*([a-z][a-z\s-]{1,30}?)(?:\.|$)",
    re.IGNORECASE,
)
_GOAL_PHRASE = re.compile(
    r"(?:business\s+)?goal\s*(?:is\s+|:)?\s*(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_CAMPAIGN_NAME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?:campaign|campagin|campagion|campagon)\s+name\s+(?:is|as|to|=)\s+(.+?)(?:\.|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:want\s+to\s+)?(?:make|set)\s+(?:the|teh)\s+"
        r"(?:campaign|campagin|campagion|campagon)\s+name\s+as\s+(.+?)(?:\.|$)",
        re.IGNORECASE,
    ),
)
_MY_PAGE = re.compile(
    r"my\s+page\s+is\s+((?:https?://)?(?:www\.)?(?:[a-z0-9-]+\.)+[a-z]{2,})",
    re.IGNORECASE,
)
_LANDING_NOT = re.compile(
    r"landing\s+page\s+(?:is\s+)?not\b",
    re.IGNORECASE,
)
_POSTER_HINT = re.compile(
    r"poster|email\s+template|in\s+(?:the\s+)?email",
    re.IGNORECASE,
)
_PRODUCT_NAME = re.compile(
    r"(?:the\s+)?(?:product|service)\s+(?:name|anem|naem|nmae)\s+(?:is\s+|:|=)\s*(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_PRODUCT_PHRASE = re.compile(
    r"(?:product|service)\s+(?:is\s+|:|=)\s*(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_PROMOTING = re.compile(
    r"(?:promoting|selling|launching|campaign\s+for)\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_REPLACE_PRODUCT = re.compile(
    r"(?:replace|change|switch)\s+(?:to\s+)?(.+?)(?:\s+instead|\s+campaign|\.|$)",
    re.IGNORECASE,
)
_CHANGE_PRODUCT = re.compile(
    r"(?:change|update|set)\s+(?:the\s+)?(?:product|service)\s+(?:to\s+|:)\s*(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_MAKING_FOR = re.compile(
    r"i\s+was\s+\w+\s+for\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_BUSINESS_IS = re.compile(
    r"my\s+business\s+is(?:\s+that)?\s+(?:i\s+)?(?:provide|offer|sell|run)\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_PROVIDE_SERVICES = re.compile(
    r"(?:i|we)\s+provide\s+(?:teh\s+|the\s+)?(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_IMAGE_ONLY_CORRECTION = re.compile(
    r"only\s+(?:want\s+)?(?:to\s+)?(?:set\s+)?(?:this\s+)?(?:as\s+)?(?:the\s+)?images?\s+url",
    re.IGNORECASE,
)

_TONE_CANONICAL = {
    "trendy": "Trendy",
    "casual": "Casual",
    "premium": "Premium",
    "professional": "Professional",
    "friendly": "Friendly",
    "luxury": "Luxury",
}


def _strip_trailing_punctuation(value: str) -> str:
    return value.strip().rstrip(".,;:!?")


def _normalize_landing_page(value: str) -> str:
    cleaned = _strip_trailing_punctuation(value)
    if not cleaned:
        return cleaned
    if cleaned.lower().startswith(("http://", "https://")):
        return cleaned
    return f"https://{cleaned.lstrip('/')}"


def _looks_like_image_url(url: str) -> bool:
    lower = url.lower()
    if re.search(r"\.(png|jpe?g|gif|webp|svg)(?:\?|$)", lower):
        return True
    return any(
        token in lower
        for token in ("/image", "/images/", "/img/", "/product", "/upload", "/media/")
    )


def _is_image_only_correction(text: str) -> bool:
    return bool(_IMAGE_ONLY_CORRECTION.search(text))


def _is_image_only_intent(text: str) -> bool:
    """True when the user is sharing a URL for the email image, not the landing page."""
    if _is_image_only_correction(text):
        return True
    lower = text.lower()
    if not (_IMAGE_HINT.search(text) or re.search(r"\bimages?\s+url\b", lower)):
        return False
    if any(
        token in lower
        for token in ("landing page", "website", "my site", "web url", "landing url", "my page")
    ):
        return False
    return bool(_HTTP_URL.search(text))


def _sanitize_product_info(value: str | None) -> str | None:
    if value is None:
        return None
    condensed = condense_product_info(str(value).strip())
    if not condensed or is_vague_product_info(condensed):
        return None
    return condensed


def _extract_audience(text: str) -> str | None:
    outreach = _OUTREACH_AUDIENCE.search(text)
    if outreach:
        value = _strip_trailing_punctuation(outreach.group(1))
        if value and len(value) < 120:
            return value

    match = _AGE_RANGE.search(text)
    if match:
        return f"Age {match.group(1)}–{match.group(2)}"
    phrase = _AUDIENCE_PHRASE.search(text)
    if phrase:
        value = _strip_trailing_punctuation(phrase.group(1))
        if value and len(value) < 120:
            return value
    if "audience" in text.lower():
        age = _AGE_RANGE.search(text)
        if age:
            return f"Age {age.group(1)}–{age.group(2)}"
    return None


def _extract_landing_page(text: str) -> str | None:
    if _is_image_only_intent(text):
        return None

    hint = _WEBSITE_HINT.search(text)
    if hint:
        return _normalize_landing_page(hint.group(1))

    lower = text.lower()
    if any(token in lower for token in ("website", "landing page", "my site", "web url")):
        for url in _HTTP_URL.findall(text):
            if not _looks_like_image_url(url):
                return _normalize_landing_page(url)
        domain_match = _DOMAIN.search(text)
        if domain_match:
            return _normalize_landing_page(domain_match.group(0))

    for url in _HTTP_URL.findall(text):
        if not _looks_like_image_url(url):
            return _normalize_landing_page(url)

    if re.search(r"\b(?:is\s+)?my\s+website\b", lower):
        domain_match = _DOMAIN.search(text)
        if domain_match:
            return _normalize_landing_page(domain_match.group(0))

    return None


def _extract_product_image(text: str) -> str | None:
    urls = _HTTP_URL.findall(text)
    if _is_image_only_intent(text) and urls:
        return _strip_trailing_punctuation(urls[0])

    for url in urls:
        if _looks_like_image_url(url):
            return _strip_trailing_punctuation(url)

    if _IMAGE_HINT.search(text) and urls:
        return _strip_trailing_punctuation(urls[0])
    return None


def _extract_tone(text: str) -> str | None:
    match = _TONE_PHRASE.search(text)
    if match:
        raw = _strip_trailing_punctuation(match.group(1)).lower()
        for key, label in _TONE_CANONICAL.items():
            if key in raw:
                return label
        return match.group(1).strip().title()
    lower = text.lower()
    for key, label in _TONE_CANONICAL.items():
        if re.search(rf"\b{re.escape(key)}\b", lower):
            return label
    return None


def _extract_cta(text: str) -> str | None:
    match = _CTA_PHRASE.search(text)
    if match:
        return _strip_trailing_punctuation(match.group(1))[:120]
    lower = text.lower()
    if "shop now" in lower:
        return "Shop Now"
    if "book" in lower and "demo" in lower:
        return "Book a Free Demo"
    return None


def _extract_it_services_product(text: str) -> str | None:
    lower = text.lower()
    if not re.search(r"\bit\s+services?\b", lower):
        return None
    if "automation" in lower:
        return "IT Services & Automation"
    return "IT Services"


def _extract_product_info(text: str) -> str | None:
    name_match = _PRODUCT_NAME.search(text)
    if name_match:
        value = _sanitize_product_info(_strip_trailing_punctuation(name_match.group(1)))
        if value and 2 <= len(value) <= 80:
            return value

    it_services = _extract_it_services_product(text)
    if it_services:
        return it_services

    for pattern in (_BUSINESS_IS, _PROVIDE_SERVICES, _MAKING_FOR):
        match = pattern.search(text)
        if match:
            value = _sanitize_product_info(_strip_trailing_punctuation(match.group(1)))
            if value and 3 <= len(value) <= 200:
                return value

    for pattern in (_CHANGE_PRODUCT, _PRODUCT_PHRASE, _PROMOTING, _REPLACE_PRODUCT):
        match = pattern.search(text)
        if match:
            value = _sanitize_product_info(_strip_trailing_punctuation(match.group(1)))
            if value and 3 <= len(value) <= 200:
                return value
    lower = text.lower()
    product_keywords = (
        "t-shirt",
        "tshirt",
        "tee",
        "polo",
        "hoodie",
        "purifier",
        "saas",
        "software",
    )
    if is_revision_message(text) or "product" in lower or "campaign for" in lower:
        for keyword in product_keywords:
            if keyword in lower:
                start = lower.find(keyword)
                snippet = text[start : start + 80].strip()
                if snippet:
                    return _strip_trailing_punctuation(snippet)
    return None


def _normalize_campaign_name_value(value: str) -> str:
    cleaned = _strip_trailing_punctuation(value)
    lower = cleaned.lower()
    for prefix in ("teh ", "the "):
        if lower.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
            break
    return cleaned


def _extract_campaign_name(text: str) -> str | None:
    for pattern in _CAMPAIGN_NAME_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        value = _normalize_campaign_name_value(match.group(1))
        if value and len(value) <= 120:
            return value
    return None


def _extract_landing_page_safe(text: str) -> str | None:
    landing = _extract_landing_page(text)
    if landing and not _looks_like_image_url(landing):
        return landing
    return None


def _extract_my_page(text: str) -> str | None:
    match = _MY_PAGE.search(text)
    if match:
        return _normalize_landing_page(match.group(1))
    lower = text.lower()
    if "my page" in lower or "my website" in lower or "my site" in lower:
        for domain in _DOMAIN.finditer(text):
            candidate = _normalize_landing_page(domain.group(0))
            if candidate and "cilory" not in candidate.lower():
                return candidate
    return None


_FIELD_CLEAR_ALIASES: dict[str, tuple[str, ...]] = {
    "campaign_name": ("campaign name", "campagion name", "campagin name", "campagon name", "name"),
    "product_info": ("product name", "product", "service"),
    "audience": ("audience", "target audience"),
    "business_goal": ("goal", "business goal"),
    "tone": ("tone", "style"),
    "cta": ("cta", "call to action", "call-to-action"),
    "landing_page": ("landing page", "website", "url", "site"),
    "product_image": ("image", "product image", "photo", "picture", "poster"),
}

_CLEAR_FIELD = re.compile(
    r"\b(?:remove|clear|delete|drop|unset)\s+(?:the\s+)?(.+?)(?:\.|$)",
    re.IGNORECASE,
)


def _extract_field_clears(text: str) -> dict[str, None]:
    """Fields the user asked to remove from the campaign brief."""
    match = _CLEAR_FIELD.search(text)
    if not match:
        return {}

    target = match.group(1).strip().lower()
    clears: dict[str, None] = {}
    for field, aliases in _FIELD_CLEAR_ALIASES.items():
        if any(alias in target for alias in aliases):
            clears[field] = None
    return clears


def _extract_explicit_updates(text: str) -> dict[str, str | None]:
    """Corrections and explicit sets — always overwrite prior values."""
    updates: dict[str, str | None] = dict(_extract_field_clears(text))
    lower = text.lower()

    name = _extract_campaign_name(text)
    if name:
        updates["campaign_name"] = name

    if _LANDING_NOT.search(text) or ("landing page" in lower and "not" in lower):
        page = _extract_my_page(text)
        if page:
            updates["landing_page"] = page
        if _POSTER_HINT.search(text):
            for url in _HTTP_URL.findall(text):
                updates["product_image"] = _strip_trailing_punctuation(url)
                break
    else:
        page = _extract_my_page(text)
        if page:
            updates["landing_page"] = page

    if _POSTER_HINT.search(text) and "product_image" not in updates:
        for url in _HTTP_URL.findall(text):
            updates["product_image"] = _strip_trailing_punctuation(url)
            break

    if "website" in lower or "landing page" in lower:
        landing = _extract_landing_page(text)
        if landing and "landing_page" not in updates:
            updates["landing_page"] = landing

    product = _extract_product_info(text)
    if product:
        updates["product_info"] = product

    if is_revision_message(text) or is_explicit_field_update(text):
        goal = _extract_business_goal(text)
        if goal:
            updates["business_goal"] = goal
        audience = _extract_audience(text)
        if audience:
            updates["audience"] = audience
        tone = _extract_tone(text)
        if tone:
            updates["tone"] = tone
        cta = _extract_cta(text)
        if cta:
            updates["cta"] = cta

    return updates


def _collect_field_updates(text: str, *, revision: bool) -> dict[str, str | None]:
    """Extract all fields mentioned in the latest user message (overwrites allowed)."""
    updates: dict[str, str | None] = dict(_extract_explicit_updates(text))

    extractors: tuple[tuple[str, object], ...] = (
        ("campaign_name", _extract_campaign_name),
        ("product_info", _extract_product_info),
        ("audience", _extract_audience),
        ("business_goal", _extract_business_goal),
        ("tone", _extract_tone),
        ("cta", _extract_cta),
        ("landing_page", _extract_landing_page_safe),
        ("product_image", _extract_product_image),
    )

    for field, extractor in extractors:
        if field in updates:
            continue
        value = extractor(text)  # type: ignore[operator]
        if value and str(value).strip():
            updates[field] = str(value).strip()

    if _is_image_only_intent(text):
        updates.pop("landing_page", None)

    if revision:
        return updates

    # Without revision keywords, only set fields clearly referenced in this message.
    lower = text.lower()
    field_triggers: dict[str, tuple[str, ...]] = {
        "campaign_name": (
            "campaign name",
            "campagion name",
            "campagin name",
            "campagon name",
            "name this campaign",
            "call it",
            "make the campaign name",
            "make teh campaign name",
        ),
        "product_info": (
            "product name",
            "product anem",
            "product naem",
            "product",
            "service",
            "services",
            "description",
            "promoting",
            "business is",
            "provide",
            "making for",
            "t-shirt",
            "tshirt",
            "purifier",
            "it service",
        ),
        "audience": (
            "audience",
            "age ",
            "target",
            "send email",
            "email to",
            "reach out",
            "founders",
            "customers",
            "users who",
        ),
        "business_goal": ("goal", "objective"),
        "tone": ("tone", "style"),
        "cta": ("cta", "call to action", "call-to-action"),
        "landing_page": ("website", "landing page", "my page", "my site"),
        "product_image": ("image", "poster", "photo", "picture"),
    }
    filtered: dict[str, str | None] = {}
    for field, value in updates.items():
        if value is None:
            filtered[field] = None
            continue
        triggers = field_triggers.get(field, ())
        if any(trigger in lower for trigger in triggers):
            filtered[field] = value
        elif field == "product_image" and value:
            filtered[field] = value
        elif field == "landing_page" and value and not _is_image_only_intent(text):
            filtered[field] = value
    return filtered


def _extract_business_goal(text: str) -> str | None:
    match = _GOAL_PHRASE.search(text)
    if match:
        return _strip_trailing_punctuation(match.group(1))[:200]
    lower = text.lower()
    if "drive website" in lower or "website visit" in lower:
        return "Drive website visits"
    if "book" in lower and "demo" in lower:
        return "Book product demos"
    return None


def extract_from_latest_user_message(
    messages: list[dict[str, str]],
    current: CampaignData,
    *,
    revision: bool | None = None,
) -> CampaignData:
    """Apply field updates from the latest user message. Mentioned fields overwrite prior values."""
    latest = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            latest = message.get("content", "").strip()
            break
    if not latest:
        return current

    is_revision = revision if revision is not None else is_revision_message(latest)
    updates = _collect_field_updates(latest, revision=is_revision)

    minimal_product = infer_product_from_minimal_message(latest)
    if minimal_product and not current.product_info:
        updates.setdefault("product_info", minimal_product)

    if "product_info" in updates:
        updates["product_info"] = _sanitize_product_info(updates.get("product_info"))

    if _is_image_only_correction(latest):
        urls = _HTTP_URL.findall(latest)
        if urls:
            image_url = _strip_trailing_punctuation(urls[0])
            updates["product_image"] = image_url
            if (
                current.landing_page
                and current.landing_page.rstrip("/").lower() == image_url.rstrip("/").lower()
            ):
                updates["landing_page"] = None
            else:
                updates.pop("landing_page", None)
    elif _is_image_only_intent(latest):
        updates.pop("landing_page", None)

    if not updates:
        return current

    return current.apply_updates(updates)
