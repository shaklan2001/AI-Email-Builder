"""Apply deterministic workflow edits from post-generation chat."""

from __future__ import annotations

import re

from app.langgraph.state import CampaignState
from app.schemas.email import GeneratedEmailContent
from app.schemas.follow_up_delay import FollowUpDelay
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.campaign_field_policy import DEFAULT_FOLLOW_UP_DELAY
from app.services.collection_preferences import (
    is_follow_up_enable_intent,
    parse_wants_follow_up,
)
from app.services.follow_up_delay import (
    follow_up_delay_from_state,
    format_wait_label,
    parse_follow_up_delay,
)
from app.services.workflow_structure import (
    build_canonical_workflow,
    build_no_follow_up_workflow,
)

_FOLLOW_UP_MENTION = re.compile(r"fol\w*[\s-]?u[o]?p?\b", re.IGNORECASE)

_DISABLE_FOLLOW_UP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"remove.*follow", re.IGNORECASE),
    re.compile(r"drop.*follow", re.IGNORECASE),
    re.compile(r"delete.*follow", re.IGNORECASE),
    re.compile(r"no\s+follow", re.IGNORECASE),
    re.compile(r"without\s+follow", re.IGNORECASE),
    re.compile(r"skip\s+follow", re.IGNORECASE),
    re.compile(
        r"(?:don'?t|do\s+not)\s+(?:want|need).*(?:follow|fol\w*up)",
        re.IGNORECASE,
    ),
    re.compile(
        r"remove.*(?:from\s+(?:the\s+)?(?:workflow|flow)|(?:the\s+)?follow)",
        re.IGNORECASE,
    ),
    re.compile(r"only\s+(?:the\s+)?initial", re.IGNORECASE),
    re.compile(r"initial\s+email\s+only", re.IGNORECASE),
)

_ENABLE_FOLLOW_UP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"add.*follow", re.IGNORECASE),
    re.compile(r"include.*follow", re.IGNORECASE),
    re.compile(r"bring.*follow", re.IGNORECASE),
    re.compile(r"put.*follow.*back", re.IGNORECASE),
    re.compile(r"back.*follow", re.IGNORECASE),
    re.compile(r"again.*follow", re.IGNORECASE),
    re.compile(r"follow.*again", re.IGNORECASE),
    re.compile(r"re-?add.*follow", re.IGNORECASE),
    re.compile(r"want.*follow", re.IGNORECASE),
    re.compile(r"need.*follow", re.IGNORECASE),
    re.compile(r"send.*follow", re.IGNORECASE),
)


def _mentions_follow_up(text: str) -> bool:
    cleaned = text.strip().lower()
    return bool(_FOLLOW_UP_MENTION.search(cleaned)) or "follow" in cleaned


def wants_to_disable_follow_up(text: str) -> bool:
    """True when the user asks to remove or skip the no-reply follow-up email."""
    cleaned = text.strip().lower()
    if not cleaned:
        return False

    if is_follow_up_enable_intent(text):
        return False

    if any(pattern.search(cleaned) for pattern in _DISABLE_FOLLOW_UP_PATTERNS):
        return True

    parsed = parse_wants_follow_up(text)
    if parsed is False and _mentions_follow_up(cleaned):
        return True

    if (
        parsed is False
        and re.search(r"remove|drop|delete", cleaned)
        and re.search(r"flow|workflow|email", cleaned)
    ):
        return True

    return False


def wants_to_enable_follow_up(text: str) -> bool:
    """True when the user asks to add or restore the no-reply follow-up path."""
    cleaned = text.strip().lower()
    if not cleaned or wants_to_disable_follow_up(text):
        return False

    if any(pattern.search(cleaned) for pattern in _ENABLE_FOLLOW_UP_PATTERNS):
        return True

    if _mentions_follow_up(cleaned) and re.search(
        r"again|change\s+my\s+mind|add|include|bring|back",
        cleaned,
    ):
        return True

    parsed = parse_wants_follow_up(text)
    if parsed is True and _mentions_follow_up(cleaned):
        return True

    return False


def wants_to_update_follow_up_delay(text: str) -> bool:
    """True when the user specifies a new wait time for an existing follow-up path."""
    if parse_follow_up_delay(text) is None:
        return False
    cleaned = text.strip().lower()
    return _mentions_follow_up(cleaned) or bool(
        re.search(r"\bwait\b|\bdelay\b|\bafter\b", cleaned),
    )


def resolve_follow_up_delay_for_edit(
    message: str,
    state: CampaignState,
) -> FollowUpDelay:
    parsed = parse_follow_up_delay(message)
    if parsed is not None:
        return parsed

    from_state = follow_up_delay_from_state(state.get("follow_up_delay"))
    if from_state is not None:
        return from_state

    return DEFAULT_FOLLOW_UP_DELAY


def _workflow_from_state(state: CampaignState) -> WorkflowDefinition | None:
    raw = state.get("workflow")
    if not isinstance(raw, dict):
        return None
    try:
        definition = WorkflowDefinition.model_validate(raw)
    except Exception:
        return None
    if not definition.steps:
        return None
    return definition


def _initial_email_step(steps: list[WorkflowStep]) -> WorkflowStep | None:
    for step in steps:
        if step.type != "send_email":
            continue
        if step.branch == "no":
            continue
        return step
    return next((s for s in steps if s.type == "send_email"), None)


def _follow_up_email_step(steps: list[WorkflowStep]) -> WorkflowStep | None:
    send_steps = [s for s in steps if s.type == "send_email"]
    if len(send_steps) > 1:
        return send_steps[-1]
    return next((s for s in steps if s.type == "send_email" and s.branch == "no"), None)


def _email_from_templates(
    state: CampaignState,
    *,
    step_id: str | None = None,
    prefer_non_initial: bool = False,
) -> GeneratedEmailContent | None:
    templates = state.get("email_templates")
    if not isinstance(templates, list):
        return None

    candidates: list[dict[str, object]] = []
    for item in templates:
        if not isinstance(item, dict):
            continue
        if step_id is not None and item.get("step_id") != step_id:
            continue
        candidates.append(item)

    if not candidates and prefer_non_initial:
        for item in templates:
            if isinstance(item, dict) and item.get("step_id") != "step_1":
                candidates.append(item)

    for item in candidates:
        subject = item.get("subject")
        html = item.get("html_content")
        plain = item.get("plain_text_content")
        if not all(isinstance(v, str) and v.strip() for v in (subject, html, plain)):
            continue
        return GeneratedEmailContent.from_ai_draft(
            subject=str(subject),
            html_content=str(html),
            plain_text_content=str(plain),
        )
    return None


def strip_follow_up_from_workflow(definition: WorkflowDefinition) -> WorkflowDefinition:
    """Remove wait + no-reply follow-up while keeping initial email and reply handling."""
    initial_step = _initial_email_step(definition.steps)
    initial_name = (
        initial_step.name.strip()
        if initial_step and isinstance(initial_step.name, str) and initial_step.name.strip()
        else "Initial Outreach"
    )
    initial_email = initial_step.email if initial_step else None

    result = build_no_follow_up_workflow(initial_name=initial_name)
    if initial_email is not None:
        result = result.model_copy(
            update={
                "steps": [
                    result.steps[0].model_copy(update={"email": initial_email}),
                    *result.steps[1:],
                ],
            },
        )

    return result.model_copy(
        update={
            "follow_up_delay": None,
            "workflow_type": definition.workflow_type or "conditional",
        },
    )


def add_follow_up_to_workflow(
    definition: WorkflowDefinition,
    delay: FollowUpDelay,
    *,
    state: CampaignState | None = None,
) -> WorkflowDefinition:
    """Rebuild the standard follow-up branch while preserving existing email drafts."""
    initial_step = _initial_email_step(definition.steps)
    prior_follow_up = _follow_up_email_step(definition.steps)

    initial_name = (
        initial_step.name.strip()
        if initial_step and isinstance(initial_step.name, str) and initial_step.name.strip()
        else "Initial Outreach"
    )
    follow_up_name = (
        prior_follow_up.name.strip()
        if prior_follow_up
        and isinstance(prior_follow_up.name, str)
        and prior_follow_up.name.strip()
        else "Follow Up"
    )

    result = build_canonical_workflow(
        delay,
        initial_name=initial_name,
        follow_up_name=follow_up_name,
    )

    initial_email = initial_step.email if initial_step else None
    follow_up_email = prior_follow_up.email if prior_follow_up else None
    if follow_up_email is None and state is not None:
        follow_up_email = _email_from_templates(
            state,
            step_id="step_6",
            prefer_non_initial=True,
        )

    updated_steps = list(result.steps)
    if initial_email is not None:
        updated_steps[0] = updated_steps[0].model_copy(update={"email": initial_email})
    if follow_up_email is not None:
        updated_steps[-1] = updated_steps[-1].model_copy(update={"email": follow_up_email})

    return result.model_copy(
        update={
            "steps": updated_steps,
            "follow_up_delay": delay,
            "workflow_type": definition.workflow_type or "conditional",
        },
    )


def workflow_has_follow_up(definition: WorkflowDefinition) -> bool:
    steps = definition.steps
    if any(s.type == "wait" for s in steps):
        return True
    if any(s.type == "no_reply_branch" for s in steps):
        return True
    send_emails = [s for s in steps if s.type == "send_email"]
    if len(send_emails) > 1:
        return True
    return any(s.type == "send_email" and s.branch == "no" for s in steps)


def follow_up_email_needs_generation(definition: WorkflowDefinition) -> bool:
    follow_up = _follow_up_email_step(definition.steps)
    return follow_up is not None and follow_up.email is None


def apply_disable_follow_up(state: CampaignState) -> dict[str, object] | None:
    """Strip follow-up from the stored workflow and persist preference."""
    definition = _workflow_from_state(state)
    if definition is None:
        return None
    if not workflow_has_follow_up(definition):
        return {
            "wants_follow_up": False,
            "follow_up_delay": None,
            "assistant_reply": (
                "Your workflow already has no follow-up email — "
                "check the Workflow tab on the right."
            ),
        }

    updated = strip_follow_up_from_workflow(definition)
    return {
        "workflow": updated.to_api_dict(),
        "wants_follow_up": False,
        "follow_up_delay": None,
        "review_status": "pending",
        "assistant_reply": (
            "Got it — I removed the follow-up email from your workflow. "
            "It now ends after the reply check. See the updated flow in the Workflow tab."
        ),
    }


def apply_enable_follow_up(
    state: CampaignState,
    message: str,
) -> dict[str, object] | None:
    """Add or restore follow-up with the requested wait timing."""
    definition = _workflow_from_state(state)
    if definition is None:
        return None

    delay = resolve_follow_up_delay_for_edit(message, state)
    wait_label = format_wait_label(delay).lower()

    if workflow_has_follow_up(definition):
        updated = add_follow_up_to_workflow(definition, delay, state=state)
        needs_email = follow_up_email_needs_generation(updated)
        return {
            "workflow": updated.to_api_dict(),
            "wants_follow_up": True,
            "follow_up_delay": delay.to_api_dict(),
            "review_status": "pending",
            "_generate_follow_up_email": needs_email,
            "assistant_reply": (
                f"Updated your workflow — recipients wait {wait_label} after the initial email, "
                "then the reply check runs with a follow-up on the No branch. "
                "See the Workflow tab on the right."
            ),
        }

    updated = add_follow_up_to_workflow(definition, delay, state=state)
    needs_email = follow_up_email_needs_generation(updated)
    return {
        "workflow": updated.to_api_dict(),
        "wants_follow_up": True,
        "follow_up_delay": delay.to_api_dict(),
        "review_status": "pending",
        "_generate_follow_up_email": needs_email,
        "assistant_reply": (
            f"Added the follow-up path back — {wait_label} after the initial email, "
            "then Reply? with AI handling on Yes and a follow-up email on No. "
            "Check the updated flow in the Workflow tab."
        ),
    }


def apply_post_generation_workflow_edit(
    state: CampaignState,
    message: str,
) -> dict[str, object] | None:
    """Apply supported workflow edits during post-generation chat."""
    if wants_to_disable_follow_up(message):
        return apply_disable_follow_up(state)

    if wants_to_enable_follow_up(message):
        return apply_enable_follow_up(state, message)

    if wants_to_update_follow_up_delay(message):
        definition = _workflow_from_state(state)
        if definition is None or not workflow_has_follow_up(definition):
            return apply_enable_follow_up(state, message)
        return apply_enable_follow_up(state, message)

    return None
