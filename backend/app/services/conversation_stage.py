from app.langgraph.state import ConversationState, campaign_data_from_state
from app.schemas.conversation_stage import ConversationStage
from app.schemas.email import GeneratedEmailContent
from app.services.campaign_field_policy import (
    is_ready_for_campaign_brief,
    missing_required_fields,
    next_field_to_collect,
    normalize_skipped_fields,
)
from app.services.follow_up_delay import follow_up_delay_from_state


def _has_workflow_steps(raw_workflow: object) -> bool:
    return (
        isinstance(raw_workflow, dict)
        and isinstance(raw_workflow.get("steps"), list)
        and len(raw_workflow["steps"]) > 0
    )


def _send_email_steps_missing_content(raw_workflow: object) -> bool:
    if not isinstance(raw_workflow, dict):
        return False
    steps = raw_workflow.get("steps")
    if not isinstance(steps, list):
        return False

    for item in steps:
        if not isinstance(item, dict) or item.get("type") != "send_email":
            continue
        raw_email = item.get("email")
        if not isinstance(raw_email, dict):
            return True
        try:
            parsed = GeneratedEmailContent.model_validate(raw_email)
            if not parsed.final_user_version.subject.strip():
                return True
        except Exception:
            subject = raw_email.get("subject")
            if not isinstance(subject, str) or not subject.strip():
                return True
    return False


def _is_post_generation_mode(state: ConversationState) -> bool:
    return bool(state.get("brief_approved")) and _has_workflow_steps(state.get("workflow"))


def _review_approved(state: ConversationState) -> bool:
    return state.get("review_status") == "approved"


def resolve_stage(state: ConversationState) -> str:
    """Derive the canonical conversation stage from state flags and artifacts."""
    brief_status = state.get("brief_status")
    if brief_status in ("pending_approval", "editing"):
        return ConversationStage.CAMPAIGN_BRIEF

    workflow = state.get("workflow")
    if state.get("brief_approved") and not _has_workflow_steps(workflow):
        return ConversationStage.WORKFLOW_GENERATION

    if _has_workflow_steps(workflow):
        if _send_email_steps_missing_content(workflow):
            return ConversationStage.EMAIL_GENERATION
        if _review_approved(state):
            return ConversationStage.ACTIVATION
        return ConversationStage.REVIEW

    campaign = campaign_data_from_state(state)
    delay = follow_up_delay_from_state(state.get("follow_up_delay"))
    skipped = normalize_skipped_fields(state.get("skipped_fields"))

    if missing_required_fields(campaign):
        return ConversationStage.DISCOVERY

    if not is_ready_for_campaign_brief(
        campaign,
        follow_up_delay=delay,
        wants_follow_up=state.get("wants_follow_up"),
        email_length=state.get("email_length"),
    ):
        raw_messages = state.get("messages")
        messages = raw_messages if isinstance(raw_messages, list) else None
        next_field = next_field_to_collect(
            campaign,
            skipped,
            include_optional=state.get("brief_status") == "editing",
            follow_up_delay=delay,
            wants_follow_up=state.get("wants_follow_up"),
            wants_cta=state.get("wants_cta"),
            email_length=state.get("email_length"),
            messages=messages,
        )
        if next_field:
            return ConversationStage.DISCOVERY

    if state.get("campaign_brief"):
        return ConversationStage.CAMPAIGN_BRIEF

    return ConversationStage.DISCOVERY


def resolve_stage_value(state: ConversationState) -> str:
    """Prefer persisted stage when still consistent with derived stage."""
    stored = state.get("current_stage")
    derived = resolve_stage(state)
    valid_stages = {member.value for member in ConversationStage}
    if isinstance(stored, str) and stored in valid_stages:
        if stored == derived:
            return stored
        if stored in (
            ConversationStage.DISCOVERY,
            ConversationStage.CAMPAIGN_BRIEF,
        ) and derived in (
            ConversationStage.DISCOVERY,
            ConversationStage.CAMPAIGN_BRIEF,
        ):
            return derived
        if stored in (
            ConversationStage.WORKFLOW_GENERATION,
            ConversationStage.EMAIL_GENERATION,
            ConversationStage.REVIEW,
            ConversationStage.ACTIVATION,
        ) and derived in (
            ConversationStage.WORKFLOW_GENERATION,
            ConversationStage.EMAIL_GENERATION,
            ConversationStage.REVIEW,
            ConversationStage.ACTIVATION,
        ):
            return derived
    return derived
