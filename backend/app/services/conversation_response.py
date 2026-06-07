"""Campaign conversation helpers — LLM prompt context and template fallbacks."""

import re

from app.langgraph.state import CampaignState, MessageDict, campaign_data_from_state
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
    condense_product_info,
    next_field_to_collect,
)
from app.services.campaign_field_policy import WANTS_CTA_FIELD, resolve_wants_cta
from app.services.campaign_naming import is_placeholder_campaign_name, suggest_campaign_name_rule
from app.services.collection_preferences import (
    CTA_LABEL_QUESTION,
    EMAIL_LENGTH_QUESTION,
    WANTS_CTA_QUESTION,
    WANTS_FOLLOW_UP_QUESTION,
    format_email_length_brief,
    format_wants_cta_brief,
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
    "product_info": (
        "What product or service is this campaign promoting? "
        "(A short name is enough — e.g. \"Freelance Mobile Development\" — not your whole pitch.)"
    ),
    "business_goal": "What is the main business goal for this campaign?",
    "audience": "Who is your target audience?",
    "tone": "What tone would you like the emails to use?",
    "wants_cta": (
        "Do you want a call-to-action button in the email? "
        "Reply yes to add one, or no to skip the button."
    ),
    "cta": (
        "What should the CTA button say? "
        "Examples: Learn More, Book a Call, Book a Demo, Get Started."
    ),
    "landing_page": "What URL should the CTA button link to?",
    "product_image": "Do you have a product image URL to include?",
    "attachments": "Do you have any files or attachments to include?",
    "competitors": "Who are your main competitors, if any?",
}

_TONE_OPTIONS = ("Trendy", "Casual", "Premium", "Professional")

COLLECTION_REPLY_SYSTEM = """You are a friendly sales campaign strategist helping plan an email outreach campaign.

Read the full conversation and reply like a natural human — warm, concise, and aware of what was already said.

STRICT rules:
- Never use checklists, ✓ bullets, progress bars, percentages, or "Campaign Setup Progress"
- Never open with "Great, I've updated your campaign" or similar template phrases
- Do not dump every known field back as a formatted list — the campaign brief is shown in the UI
- NEVER write email drafts in chat — no subject lines, no email body, no "Initial Email" blocks
- Emails and workflow are built by the app and shown in the Workflow and Emails tabs on the right — not in chat
- Briefly acknowledge what the user just shared (one short phrase is enough)
- Ask exactly ONE follow-up question when more info is needed — weave it naturally into your reply
- Keep the whole reply to 2–4 short sentences
- When offering choices (tone, email length), mention them casually — not "I have one question:"
- For optional fields, mention they can say skip, not sure, or you decide
- Ask whether the user wants a CTA button before asking for the button label or URL
- When the user says yes to a CTA, ask what the button should say before asking for the URL
- When the user says no to a CTA, accept it — do NOT re-offer a button, Learn More, or any CTA label
- When "Already configured" lists CTA as skipped/no button, never mention CTAs again
- When a CTA label is set, always ask for the CTA URL before the brief is ready
- Do not ask for product image URLs unless the user wants an image in the email
- For product/service (required), be gentle but clear it is needed if still missing
- When enough info is collected, tell them to check the campaign brief on the right — do not generate content yourself
- NEVER re-ask about details already listed under "Already configured" in the prompt
- NEVER repeat confirmations for a field the user already answered or delegated — move to the next question
- If "Next detail to collect" is provided, you MUST ask about that — do not say the brief is ready unless told to"""

POST_GENERATION_REPLY_SYSTEM = """You are a sales campaign strategist. The user's workflow and emails are already built.

Answer in one or two short sentences. Help with review, workflow changes, or activation.
Never tell the user to manually add blocks, CTAs, images, or workflow steps — you are the builder.
Never regenerate the full workflow unless asked.
NEVER paste email subject lines or full email body in chat — point them to the Emails tab on the right.
NEVER re-ask about settings already listed under "Already configured" (follow-up timing, email length, etc.).
If the user gives positive feedback (looks good, cool, love it), thank them briefly and point to the Emails or Workflow tabs — do not ask new setup questions."""

BRIEF_REPLY_SYSTEM = """You are a friendly sales campaign strategist. The user has provided enough campaign details.

Reply naturally in 2–3 short sentences. Tell them their campaign brief is ready to review on the right panel.
If defaults were applied, mention them briefly in plain language — no checklists or ✓ bullets.
Invite them to say if anything should change, or to approve when it looks good.
NEVER write email drafts, subject lines, or email body copy in chat — those are generated after approval and shown in the Emails tab."""

BRIEF_UPDATE_REPLY_SYSTEM = """You are a friendly sales campaign strategist. The user revised their campaign brief.

Reply naturally in 2–3 short sentences. Acknowledge what changed in plain language — no checklists or ✓ bullets.
Point them to the updated brief on the right and invite further edits or approval."""

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
    wants_cta: object = None,
    email_length: object = None,
    messages: list[MessageDict] | None = None,
) -> str | None:
    skipped = skipped_fields or set()
    return next_field_to_collect(
        campaign,
        skipped,
        include_optional=editing_brief,
        follow_up_delay=follow_up_delay,
        wants_follow_up=wants_follow_up,
        wants_cta=wants_cta,
        email_length=email_length,
        messages=messages,
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


def _strip_question_prefix(text: str) -> str:
    for prefix in ("I have one question:\n\n", "I need one required detail:\n\n"):
        if text.startswith(prefix):
            return text[len(prefix) :]
    return text


def _follow_up_question(field: str) -> str:
    if field == EMAIL_LENGTH_FIELD:
        return f"I have one question:\n\n{EMAIL_LENGTH_QUESTION}"
    if field == WANTS_FOLLOW_UP_FIELD:
        return f"I have one question:\n\n{WANTS_FOLLOW_UP_QUESTION}"
    if field == WANTS_CTA_FIELD:
        return f"I have one question:\n\n{WANTS_CTA_QUESTION}"
    if field == FOLLOW_UP_DELAY_FIELD:
        return f"I have one question:\n\n{FOLLOW_UP_DELAY_QUESTION}"
    question = _FIELD_QUESTIONS.get(field, "What else should I know for this campaign?")
    if field == REQUIRED_FIELD:
        return (
            "I need one required detail:\n\n"
            f"{question}\n\n"
            "(Give a short product or service name — a few words is enough; we'll ask about audience separately.)"
        )
    if field == "tone":
        options = "\n".join(f"• {option}" for option in _TONE_OPTIONS)
        return (
            f"I have one question:\n\n{question}\n\n{options}\n\n"
            "(Say skip, not sure, or recommend for me if you'd like a default.)"
        )
    if field == "cta":
        return (
            f"I have one question:\n\n{CTA_LABEL_QUESTION}\n\n"
            "(Say you decide for Learn More, or describe the action — e.g. book a call.)"
        )
    if field == "landing_page":
        return f"I have one question:\n\n{question}"
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
    wants_cta: bool | None = None,
    email_length: str | None = None,
    email_length_words: int | None = None,
    reply_handling: str | None = None,
    skipped_fields: set[str] | None = None,
    state_only: bool = False,
) -> CampaignBriefData:
    skipped = skipped_fields or set()
    campaign = apply_field_defaults(campaign, skipped, wants_cta=wants_cta)
    resolved_landing = landing_page or _field_value(campaign, "landing_page")
    resolved_image = product_image or _field_value(campaign, "product_image")

    resolved_follow_up_delay: str | None
    if wants_follow_up is False:
        resolved_follow_up_delay = "None — initial email only"
    else:
        resolved_follow_up_delay = _resolve_follow_up_delay_brief(
            messages,
            follow_up_delay=follow_up_delay,
        )

    resolved_cta: str | None
    if wants_cta is False:
        resolved_cta = "None — no CTA button"
    elif wants_cta is True:
        resolved_cta = _field_value(campaign, "cta") or "Learn More"
    else:
        resolved_cta = _field_value(campaign, "cta")

    raw_product = _field_value(campaign, "product_info")
    resolved_product = condense_product_info(raw_product) if raw_product else None
    if not resolved_product:
        resolved_product = raw_product

    resolved_name = campaign_name
    if is_placeholder_campaign_name(resolved_name):
        resolved_name = suggest_campaign_name_rule(campaign) or resolved_name

    return CampaignBriefData(
        campaign_name=resolved_name,
        audience=_field_value(campaign, "audience"),
        product_info=resolved_product,
        tone=_field_value(campaign, "tone"),
        cta=resolved_cta,
        landing_page=resolved_landing if wants_cta is True else None,
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
    ]
    if brief.landing_page and str(brief.landing_page).strip():
        lines.extend(["", f"CTA URL:\n{brief.landing_page.strip()}"])
    lines.extend([
        "",
        f"Tone:\n{_not_provided(brief.tone)}",
        "",
        f"Email Length:\n{_not_provided(brief.email_length)}",
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
    ])
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
    "landingPage": "CTA URL",
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
        "Happy to use defaults for the rest — I just need to know what product or service "
        f"you're promoting. {_strip_question_prefix(_follow_up_question(REQUIRED_FIELD))}"
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
    wants_cta: object = None,
) -> list[str]:
    lines: list[str] = []
    if isinstance(email_length, str) and email_length.strip():
        words = email_length_words if isinstance(email_length_words, int) else None
        lines.append(
            f"✓ Email Length: {format_email_length_brief(email_length, words=words)}",
        )
    if isinstance(wants_follow_up, bool):
        lines.append(f"✓ Follow-Up: {format_wants_follow_up_brief(wants_follow_up)}")
    if wants_cta is False:
        lines.append(f"✓ CTA: {format_wants_cta_brief(wants_cta)}")
    elif wants_cta is True:
        lines.append(f"✓ CTA: {format_wants_cta_brief(wants_cta)}")
    return lines


def build_collection_prompt_context(
    campaign: CampaignData,
    messages: list[MessageDict],
    *,
    editing_brief: bool = False,
    skipped_fields: set[str] | None = None,
    follow_up_delay: object = None,
    wants_follow_up: object = None,
    wants_cta: object = None,
    email_length: object = None,
    email_length_words: object = None,
) -> str:
    """Build user prompt for natural LLM collection replies."""
    skipped = skipped_fields or set()
    effective_wants_cta = resolve_wants_cta(wants_cta, skipped)
    sections: list[str] = []

    history = "\n".join(
        f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
        for m in messages[-12:]
    )
    sections.append(f"Conversation:\n{history}")

    known: list[str] = []
    for field, label in _COLLECTED_DISPLAY:
        value = _field_value(campaign, field)
        if not value:
            continue
        if field == "product_image":
            known.append(f"- {label}: provided")
        else:
            known.append(f"- {label}: {value}")
    known.extend(
        line.replace("✓ ", "- ")
        for line in _preference_confirmed_lines(
            email_length=email_length,
            email_length_words=email_length_words,
            wants_follow_up=wants_follow_up,
            wants_cta=effective_wants_cta,
        )
    )
    delay = follow_up_delay_from_state(follow_up_delay)
    if delay is not None:
        known.append(f"- Follow-Up Delay: {format_follow_up_delay_brief(delay)}")
    if effective_wants_cta is False:
        known.append("- CTA: skipped (no button — do not mention again)")
    sections.append(
        "Already configured:\n" + ("\n".join(known) if known else "(just getting started)"),
    )

    next_field = next_missing_field(
        campaign,
        skipped,
        editing_brief=editing_brief,
        follow_up_delay=follow_up_delay,
        wants_follow_up=wants_follow_up,
        wants_cta=effective_wants_cta,
        email_length=email_length,
        messages=messages,
    )
    if next_field:
        sections.append(
            "Next detail to collect (ask naturally, one question only):\n"
            f"{_strip_question_prefix(_follow_up_question(next_field))}",
        )
        if effective_wants_cta is False and next_field not in (WANTS_CTA_FIELD, "cta", "landing_page"):
            sections.append(
                "Reminder: the user declined a CTA button — do not mention buttons, "
                "Learn More, or CTA labels in your reply.",
            )
    elif editing_brief:
        sections.append("The user is editing their brief. Ask what they would like to change.")
    elif _field_value(campaign, REQUIRED_FIELD):
        assumptions = build_assumptions_block(campaign)
        if assumptions:
            sections.append(f"Defaults in use:\n{assumptions}")
        sections.append(
            "All required info is collected. Tell them the campaign brief is ready "
            "on the right panel — they can choose Looks Good to generate the workflow "
            "or Edit Campaign Details to change anything. Do NOT ask another setup question.",
        )
    else:
        sections.append("Still missing the product or service — ask for it naturally.")

    return "\n\n".join(sections)


def build_post_generation_prompt_context(
    state: CampaignState,
    messages: list[MessageDict],
) -> str:
    """Build user prompt for post-generation chat — includes persisted LangGraph state."""
    sections: list[str] = []

    history = "\n".join(
        f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
        for m in messages[-8:]
    )
    sections.append(f"Recent conversation:\n{history}")

    configured: list[str] = []
    campaign = apply_field_defaults(campaign_data_from_state(state))
    if campaign.product_info:
        configured.append(f"- Product: {campaign.product_info}")
    if isinstance(state.get("email_length"), str):
        words = state.get("email_length_words")
        configured.append(
            f"- Email Length: {format_email_length_brief(state['email_length'], words=words if isinstance(words, int) else None)}",
        )
    if isinstance(state.get("wants_follow_up"), bool):
        configured.append(
            f"- Follow-Up: {format_wants_follow_up_brief(state['wants_follow_up'])}",
        )
    delay = follow_up_delay_from_state(state.get("follow_up_delay"))
    if delay is not None:
        configured.append(f"- Follow-Up Delay: {format_follow_up_delay_brief(delay)}")
    if state.get("review_status"):
        configured.append(f"- Review Status: {state['review_status']}")
    sections.append(
        "Already configured (do NOT ask about these again):\n"
        + ("\n".join(configured) if configured else "- (see workflow)"),
    )

    raw_workflow = state.get("workflow")
    if isinstance(raw_workflow, dict) and isinstance(raw_workflow.get("steps"), list):
        steps = [
            WorkflowStep.model_validate(item)
            for item in raw_workflow["steps"]
            if isinstance(item, dict)
        ]
        if steps:
            sections.append(build_workflow_summary(WorkflowDefinition(steps=steps)))

    latest_user = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            latest_user = str(message.get("content", "")).strip()
            break
    if latest_user:
        sections.append(f"Latest user message: {latest_user}")

    return "\n\n".join(sections)


def build_collection_fallback_reply(
    campaign: CampaignData,
    *,
    editing_brief: bool = False,
    skipped_fields: set[str] | None = None,
    follow_up_delay: object = None,
    wants_follow_up: object = None,
    wants_cta: object = None,
    email_length: object = None,
    email_length_words: object = None,
    messages: list[MessageDict] | None = None,
) -> str:
    """Minimal fallback when the LLM is unavailable."""
    skipped = skipped_fields or set()
    next_field = next_missing_field(
        campaign,
        skipped,
        editing_brief=editing_brief,
        follow_up_delay=follow_up_delay,
        wants_follow_up=wants_follow_up,
        wants_cta=wants_cta,
        email_length=email_length,
        messages=messages,
    )
    if next_field:
        return _strip_question_prefix(_follow_up_question(next_field))
    if editing_brief:
        return "What would you like to change about your campaign?"
    assumptions = build_assumptions_block(campaign)
    if assumptions:
        return (
            "I've got a good picture of your campaign. "
            "Want to tweak any of the defaults before I finalize the brief?"
        )
    return "Looks like I have what I need — check the campaign brief on the right when you're ready."


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
    """Backward-compatible alias for tests and LLM fallback."""
    return build_collection_fallback_reply(
        campaign,
        editing_brief=editing_brief,
        skipped_fields=skipped_fields,
        follow_up_delay=follow_up_delay,
        wants_follow_up=wants_follow_up,
        email_length=email_length,
        email_length_words=email_length_words,
    )


def build_brief_reply_context(
    campaign: CampaignData,
    messages: list[MessageDict],
    *,
    changes: list[str] | None = None,
) -> str:
    sections: list[str] = []
    history = "\n".join(
        f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
        for m in messages[-8:]
    )
    sections.append(f"Recent conversation:\n{history}")
    if changes:
        sections.append("Brief changes:\n" + "\n".join(f"- {change}" for change in changes))
    assumptions = build_assumptions_block(campaign)
    if assumptions:
        sections.append(f"Defaults applied:\n{assumptions}")
    sections.append(
        "The campaign brief panel is visible on the right. "
        "User can approve or request edits.",
    )
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
