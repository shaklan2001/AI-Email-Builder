"""Structured strategist replies for campaign setup and post-generation UX."""

import re

from app.langgraph.state import MessageDict
from app.schemas.campaign import CampaignData
from app.schemas.campaign_brief import (
    DEFAULT_REPLY_HANDLING,
    DEFAULT_TOOLS_AVAILABLE,
    CampaignBriefData,
)
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.schemas.follow_up_delay import FollowUpDelay
from app.services.campaign_field_policy import (
    EMAIL_LENGTH_FIELD,
    FIELD_LABELS,
    FOLLOW_UP_DELAY_FIELD,
    REQUIRED_FIELD,
    WANTS_FOLLOW_UP_FIELD,
    apply_field_defaults,
    assumption_lines,
    next_field_to_collect,
)
from app.services.collection_preferences import (
    EMAIL_LENGTH_QUESTION,
    WANTS_FOLLOW_UP_QUESTION,
    format_email_length_brief,
    format_wants_follow_up_brief,
)
from app.services.follow_up_delay import (
    FOLLOW_UP_DELAY_QUESTION,
    follow_up_delay_from_state,
    format_follow_up_delay_brief,
    format_wait_label,
    parse_follow_up_delay,
)

_FIELD_QUESTIONS: dict[str, str] = {
    "campaign_name": "What would you like to name this campaign?",
    "product_info": "What product or service is this campaign promoting?",
    "business_goal": "What is the main business goal for this campaign?",
    "audience": "Who is your target audience?",
    "tone": "What tone would you like the emails to use?",
    "cta": "What call-to-action should recipients take?",
    "landing_page": "What landing page or website URL should we use?",
    "product_image": "Do you have a product image URL to include?",
    "attachments": "Do you have any files or attachments to include?",
    "competitors": "Who are your main competitors, if any?",
}

_TONE_OPTIONS = ("Trendy", "Casual", "Premium", "Professional")

_COLLECTED_DISPLAY: tuple[tuple[str, str], ...] = (
    ("campaign_name", "Campaign Name"),
    ("product_info", "Product"),
    ("audience", "Audience"),
    ("landing_page", "Website"),
    ("product_image", "Product Image"),
    ("attachments", "Attachments"),
    ("competitors", "Competitors"),
    ("business_goal", "Goal"),
    ("tone", "Tone"),
    ("cta", "CTA"),
)


def progress_percent(campaign: CampaignData) -> int:
    return 100 if _field_value(campaign, REQUIRED_FIELD) else 0


def progress_bar(percent: int) -> str:
    filled = max(0, min(10, round(percent / 10)))
    return "█" * filled + "░" * (10 - filled)


def _field_value(campaign: CampaignData, field: str) -> str | None:
    value = getattr(campaign, field, None)
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def next_missing_field(
    campaign: CampaignData,
    skipped_fields: set[str] | None = None,
    *,
    editing_brief: bool = False,
    follow_up_delay: object = None,
    wants_follow_up: object = None,
    email_length: object = None,
) -> str | None:
    skipped = skipped_fields or set()
    return next_field_to_collect(
        campaign,
        skipped,
        include_optional=editing_brief,
        follow_up_delay=follow_up_delay,
        wants_follow_up=wants_follow_up,
        email_length=email_length,
    )


def _confirmed_lines(campaign: CampaignData) -> list[str]:
    lines: list[str] = []
    for field, label in _COLLECTED_DISPLAY:
        value = _field_value(campaign, field)
        if not value:
            continue
        if field == "product_image":
            lines.append(f"✓ {label}: Added")
        else:
            lines.append(f"✓ {label}: {value}")
    return lines


def _follow_up_question(field: str) -> str:
    if field == EMAIL_LENGTH_FIELD:
        return f"I have one question:\n\n{EMAIL_LENGTH_QUESTION}"
    if field == WANTS_FOLLOW_UP_FIELD:
        return f"I have one question:\n\n{WANTS_FOLLOW_UP_QUESTION}"
    if field == FOLLOW_UP_DELAY_FIELD:
        return f"I have one question:\n\n{FOLLOW_UP_DELAY_QUESTION}"
    question = _FIELD_QUESTIONS.get(field, "What else should I know for this campaign?")
    if field == REQUIRED_FIELD:
        return (
            "I need one required detail:\n\n"
            f"{question}\n\n"
            "(Product / service is required — you can also describe your business in a few words.)"
        )
    if field == "tone":
        options = "\n".join(f"• {option}" for option in _TONE_OPTIONS)
        return (
            f"I have one question:\n\n{question}\n\n{options}\n\n"
            "(Say skip, not sure, or recommend for me if you'd like a default.)"
        )
    if field != REQUIRED_FIELD:
        return (
            f"I have one question:\n\n{question}\n\n"
            "(Optional — say skip, not sure, or recommend for me to use a sensible default.)"
        )
    return f"I have one question:\n\n{question}"


def _not_provided(value: str | None) -> str:
    if value and str(value).strip():
        return str(value).strip()
    return "Not provided"


def _looks_like_image_url(url: str) -> bool:
    lower = url.lower()
    if re.search(r"\.(png|jpe?g|gif|webp|svg)(?:\?|$)", lower):
        return True
    return any(
        token in lower
        for token in ("/image", "/images/", "/img/", "/product", "/upload", "/media/", "/polo")
    )


def _find_website_url_in_messages(messages: list[MessageDict]) -> str | None:
    url_pattern = re.compile(r"https?://[^\s)>\"']+", re.IGNORECASE)
    domain_pattern = re.compile(
        r"\b(?:https?://)?(?:www\.)?"
        r"([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b",
        re.IGNORECASE,
    )
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        for match in url_pattern.finditer(content):
            url = match.group(0).rstrip(".,;")
            if not _looks_like_image_url(url):
                return url
        for match in domain_pattern.finditer(content):
            domain = match.group(0).rstrip(".,;")
            if not _looks_like_image_url(domain):
                if domain.lower().startswith(("http://", "https://")):
                    return domain
                return f"https://{domain.lstrip('/')}"
    return None


def _resolve_follow_up_delay_brief(
    messages: list[MessageDict],
    *,
    follow_up_delay: object = None,
) -> str | None:
    delay = follow_up_delay_from_state(follow_up_delay)
    if delay is not None:
        return format_follow_up_delay_brief(delay)
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        parsed = parse_follow_up_delay(message.get("content", ""))
        if parsed is not None:
            return format_follow_up_delay_brief(parsed)
    return None


def build_campaign_brief(
    campaign: CampaignData,
    *,
    campaign_name: str | None,
    messages: list[MessageDict],
    product_image: str | None = None,
    landing_page: str | None = None,
    follow_up_delay: object = None,
    wants_follow_up: bool | None = None,
    email_length: str | None = None,
    email_length_words: int | None = None,
    reply_handling: str | None = None,
    state_only: bool = False,
) -> CampaignBriefData:
    campaign = apply_field_defaults(campaign)
    resolved_landing = landing_page or _field_value(campaign, "landing_page")
    if not state_only and not resolved_landing:
        resolved_landing = _find_website_url_in_messages(messages)

    resolved_image = product_image or _field_value(campaign, "product_image")
    if not state_only and not resolved_image:
        for message in reversed(messages):
            if message.get("role") != "user":
                continue
            content = message.get("content", "").lower()
            if any(
                token in content
                for token in ("image", "poster", "photo", "picture", "img")
            ):
                resolved_image = message.get("content", "").strip()[:500] or None
                break

    resolved_follow_up_delay: str | None
    if wants_follow_up is False:
        resolved_follow_up_delay = "None — initial email only"
    else:
        resolved_follow_up_delay = _resolve_follow_up_delay_brief(
            messages,
            follow_up_delay=follow_up_delay,
        )

    return CampaignBriefData(
        campaign_name=campaign_name,
        audience=_field_value(campaign, "audience"),
        product_info=_field_value(campaign, "product_info"),
        tone=_field_value(campaign, "tone"),
        cta=_field_value(campaign, "cta"),
        landing_page=resolved_landing,
        image_url=resolved_image,
        email_length=format_email_length_brief(
            email_length,
            words=email_length_words,
        ),
        follow_up_enabled=format_wants_follow_up_brief(wants_follow_up),
        follow_up_delay=resolved_follow_up_delay,
        reply_handling=reply_handling or DEFAULT_REPLY_HANDLING,
        tools_available=list(DEFAULT_TOOLS_AVAILABLE),
    )


def format_campaign_brief_text(brief: CampaignBriefData) -> str:
    tool_lines = [f"✓ {tool}" for tool in brief.tools_available]
    lines = [
        "Campaign Brief",
        "",
        f"Campaign Name:\n{_not_provided(brief.campaign_name)}",
        "",
        f"Product:\n{_not_provided(brief.product_info)}",
        "",
        f"Audience:\n{_not_provided(brief.audience)}",
        "",
        f"CTA:\n{_not_provided(brief.cta)}",
        "",
        f"Tone:\n{_not_provided(brief.tone)}",
        "",
        f"Email Length:\n{_not_provided(brief.email_length)}",
        "",
        f"Landing Page:\n{_not_provided(brief.landing_page)}",
        "",
        f"Image URL:\n{_not_provided(brief.image_url)}",
        "",
        f"Follow-Up Email:\n{_not_provided(brief.follow_up_enabled)}",
        "",
        f"Follow-Up Delay:\n{_not_provided(brief.follow_up_delay)}",
        "",
        f"Reply Handling:\n{_not_provided(brief.reply_handling)}",
        "",
        "Tools:",
        "",
        *(tool_lines or ["✓ Company Information", "✓ Demo Booking"]),
    ]
    return "\n".join(lines)


def build_assumptions_block(campaign: CampaignData) -> str:
    lines = assumption_lines(campaign)
    if not lines:
        return ""
    return "Assumptions:\n" + "\n".join(lines)


def build_brief_approval_reply(campaign: CampaignData | None = None) -> str:
    sections = ["Perfect. I now have enough information to build your campaign."]

    if campaign is not None:
        assumptions = build_assumptions_block(campaign)
        if assumptions:
            sections.append(assumptions)
            sections.append(
                "Would you like to customize any of these before generating the campaign? "
                "You can share changes in chat, or review the Campaign Brief on the right.",
            )

    sections.append(
        "Review your Campaign Brief on the right. "
        "Choose Looks Good to generate your workflow, "
        "or Edit Campaign Details if something needs to change.",
    )
    return "\n\n".join(sections)


_BRIEF_CHANGE_LABELS: dict[str, str] = {
    "campaignName": "Campaign Name",
    "productInfo": "Product",
    "audience": "Audience",
    "tone": "Tone",
    "cta": "CTA",
    "landingPage": "Landing Page",
    "imageUrl": "Image URL",
    "emailLength": "Email Length",
    "followUpEnabled": "Follow-Up Email",
    "followUpDelay": "Follow-Up Delay",
    "replyHandling": "Reply Handling",
}


def detect_brief_changes(
    previous: dict[str, object] | None,
    brief: CampaignBriefData,
) -> list[str]:
    if not previous:
        return []
    current = brief.to_api_dict()
    changes: list[str] = []
    for key, label in _BRIEF_CHANGE_LABELS.items():
        old_raw = previous.get(key)
        new_raw = current.get(key)
        if isinstance(new_raw, list):
            continue
        old_val = str(old_raw).strip() if old_raw is not None else ""
        new_val = str(new_raw).strip() if new_raw is not None else ""
        if not new_val or new_val == old_val:
            continue
        if old_val.lower() in ("", "not provided") and new_val:
            changes.append(f"{label}: {new_val}")
        elif old_val and new_val != old_val:
            changes.append(f"{label}: {new_val}")
    return changes


def build_brief_update_reply(changes: list[str]) -> str:
    if not changes:
        return build_brief_approval_reply()
    lines = [
        "Great, I've updated your campaign brief.",
        "",
        *[f"✓ {change}" for change in changes],
        "",
        "Review the updated Campaign Brief on the right. "
        "Choose Looks Good when you're ready, or Edit Campaign Details for more changes.",
    ]
    return "\n".join(lines)


def build_product_required_after_skip() -> str:
    return (
        "I still need your product or service before I can build the campaign — "
        "that one can't be skipped.\n\n"
        f"{_follow_up_question(REQUIRED_FIELD)}"
    )


def build_brief_edit_reply() -> str:
    return (
        "No problem — tell me what you'd like to change about your campaign "
        "and I'll update the brief."
    )


def _preference_confirmed_lines(
    *,
    email_length: object = None,
    email_length_words: object = None,
    wants_follow_up: object = None,
) -> list[str]:
    lines: list[str] = []
    if isinstance(email_length, str) and email_length.strip():
        words = email_length_words if isinstance(email_length_words, int) else None
        lines.append(
            f"✓ Email Length: {format_email_length_brief(email_length, words=words)}",
        )
    if isinstance(wants_follow_up, bool):
        lines.append(f"✓ Follow-Up: {format_wants_follow_up_brief(wants_follow_up)}")
    return lines


def build_collection_reply(
    campaign: CampaignData,
    *,
    editing_brief: bool = False,
    skipped_fields: set[str] | None = None,
    follow_up_delay: object = None,
    wants_follow_up: object = None,
    email_length: object = None,
    email_length_words: object = None,
) -> str:
    """Confirm understanding, show progress, ask at most one follow-up question."""
    skipped = skipped_fields or set()
    confirmed = _confirmed_lines(campaign)
    percent = progress_percent(campaign)
    bar = progress_bar(percent)

    sections: list[str] = []

    preference_lines = _preference_confirmed_lines(
        email_length=email_length,
        email_length_words=email_length_words,
        wants_follow_up=wants_follow_up,
    )

    if confirmed or preference_lines:
        sections.append("Great, I've updated your campaign.")
        if confirmed:
            sections.append("\n".join(confirmed))
        if preference_lines:
            sections.append("\n".join(preference_lines))
    else:
        sections.append(
            "I'm starting your campaign setup — share what you know and I'll guide you step by step.",
        )

    sections.append(f"Campaign Setup Progress\n\n{bar} {percent}%")

    next_field = next_missing_field(
        campaign,
        skipped,
        editing_brief=editing_brief,
        follow_up_delay=follow_up_delay,
        wants_follow_up=wants_follow_up,
        email_length=email_length,
    )
    if next_field:
        sections.append(_follow_up_question(next_field))
    elif editing_brief:
        sections.append("What would you like to change about your campaign?")
    elif _field_value(campaign, REQUIRED_FIELD):
        product_label = FIELD_LABELS[REQUIRED_FIELD]
        product_value = _field_value(campaign, REQUIRED_FIELD)
        sections.append(f"✓ {product_label}: {product_value}")
        assumptions = build_assumptions_block(campaign)
        if assumptions:
            sections.append(assumptions)
        sections.append(
            "Would you like me to customize any of these before generating the campaign?"
        )
    else:
        sections.append("Perfect. I now have enough information to build your campaign.")

    return "\n\n".join(sections)


def _step_summary_label(
    step: WorkflowStep,
    *,
    follow_up_delay: FollowUpDelay | None = None,
) -> str:
    if step.type == "send_email":
        return step.name or "Send Email"
    if step.type == "wait":
        if step.value is not None and step.unit is not None:
            return format_wait_label(FollowUpDelay(value=step.value, unit=step.unit))
        if follow_up_delay is not None:
            return format_wait_label(follow_up_delay)
        if step.days is not None:
            day_word = "Day" if step.days == 1 else "Days"
            return f"Wait {step.days} {day_word}"
        return "Wait"
    if step.type == "reply_condition":
        return "Reply?"
    if step.type == "interested_branch":
        return step.name or "AI Reply Agent"
    if step.type == "no_reply_branch":
        return "No Reply"
    if step.type == "condition" and step.condition:
        words = step.condition.replace("_", " ")
        return words[0].upper() + words[1:] + "?"
    if step.type == "end":
        return "End"
    return step.name or step.type


def build_workflow_summary(definition: WorkflowDefinition) -> str:
    """Text diagram of the workflow for chat (spec Workflow Generation UX)."""
    delay = definition.follow_up_delay
    steps = definition.steps
    if not steps:
        return "Workflow Summary\n(No steps yet)"

    lines: list[str] = ["Workflow Summary", ""]
    condition_index = next(
        (
            i
            for i, s in enumerate(steps)
            if s.type == "reply_condition"
            or (s.type == "condition" and s.condition == "reply_received")
        ),
        -1,
    )

    if condition_index >= 0:
        before = steps[:condition_index]
        condition_step = steps[condition_index]
        after = steps[condition_index + 1 :]
        uses_generation = any(
            s.type in ("interested_branch", "no_reply_branch") for s in after
        )
        if uses_generation:
            yes_steps = [s for s in after if s.type == "interested_branch"]
            no_steps = [s for s in after if s.type == "send_email"]
            unbranched: list[WorkflowStep] = []
        else:
            yes_steps = [s for s in after if s.branch == "yes"]
            no_steps = [s for s in after if s.branch == "no"]
            unbranched = [s for s in after if not s.branch]

        if not yes_steps and unbranched:
            yes_steps = [unbranched[0]]
        if not no_steps and len(unbranched) > 1:
            no_steps = [unbranched[1]]
        elif not no_steps and len(unbranched) == 1 and not yes_steps:
            no_steps = unbranched

        for i, step in enumerate(before):
            if i > 0:
                lines.append("↓")
            lines.append(_step_summary_label(step, follow_up_delay=delay))

        if before:
            lines.append("↓")
        lines.append(_step_summary_label(condition_step, follow_up_delay=delay))
        lines.append("")
        if yes_steps:
            lines.append(
                "├─ Yes → "
                + " → ".join(_step_summary_label(s, follow_up_delay=delay) for s in yes_steps)
            )
        if no_steps:
            lines.append(
                "└─ No → "
                + " → ".join(_step_summary_label(s, follow_up_delay=delay) for s in no_steps)
            )
    else:
        for i, step in enumerate(steps):
            if i > 0:
                lines.append("↓")
            lines.append(_step_summary_label(step, follow_up_delay=delay))

    return "\n".join(lines)


def build_post_generation_reply(
    definition: WorkflowDefinition,
    *,
    email_count: int,
) -> str:
    summary = build_workflow_summary(definition)
    email_line = (
        f"- Email Templates ({email_count} drafted)"
        if email_count
        else "- Email Templates"
    )
    return "\n\n".join(
        [
            "Perfect. I now have enough information to build your campaign.",
            summary,
            "Generated Assets\n\n- Workflow\n"
            f"{email_line}\n"
            "- Recipient Strategy",
            "What would you like to do next?\n\n"
            "- Review Emails\n"
            "- Modify Workflow\n"
            "- Activate Campaign",
        ],
    )
