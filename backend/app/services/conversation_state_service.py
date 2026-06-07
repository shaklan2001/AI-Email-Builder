from copy import deepcopy

from app.langgraph.state import ConversationState, campaign_data_from_state
from app.schemas.conversation_stage import (
    STAGES_WITH_BRIEF_PREVIEW,
    STAGES_WITH_WORKFLOW_PREVIEW,
    ConversationStage,
)
from app.services.approval_status import sync_approval_fields
from app.services.campaign_field_policy import compute_collection_missing_fields
from app.services.conversation_stage import resolve_stage, resolve_stage_value


def empty_conversation_state(*, user_id: str, workflow_id: str) -> ConversationState:
    state: ConversationState = {
        "campaign_id": workflow_id,
        "workflow_id": workflow_id,
        "user_id": user_id,
        "thread_id": workflow_id,
        "messages": [],
        "campaign_brief": None,
        "workflow": None,
        "email_templates": [],
        "recipients": [],
        "missing_fields": [],
        "current_stage": ConversationStage.DISCOVERY,
        "approval_status": "collecting",
        "campaign_name": None,
        "business_goal": None,
        "product_info": None,
        "audience": None,
        "tone": None,
        "cta": None,
        "landing_page": None,
        "product_image": None,
        "attachments": None,
        "competitors": None,
        "follow_up_strategy": None,
        "follow_up_delay": None,
        "wants_follow_up": None,
        "wants_cta": None,
        "email_length": None,
        "email_length_words": None,
        "reply_strategy": None,
        "skipped_fields": [],
        "brief_status": None,
        "brief_approved": False,
        "review_status": None,
        "regenerate_workflow": False,
        "leads": {},
        "conversation_threads": [],
        "reply_intent": None,
        "tool_calls": [],
        "lead_status": None,
        "generated_responses": [],
    }
    return normalize_conversation_state(state)


def compute_missing_fields(state: ConversationState) -> list[str]:
    return compute_collection_missing_fields(state)


def email_templates_from_workflow(workflow: dict[str, object]) -> list[dict[str, object]]:
    steps = workflow.get("steps")
    if not isinstance(steps, list):
        return []

    templates: list[dict[str, object]] = []
    for item in steps:
        if not isinstance(item, dict) or item.get("type") != "send_email":
            continue
        step_id = item.get("id")
        raw_email = item.get("email")
        if not isinstance(step_id, str) or not isinstance(raw_email, dict):
            continue
        final = raw_email.get("final_user_version")
        if isinstance(final, dict):
            subject = final.get("subject")
            html = final.get("html_content")
            plain = final.get("plain_text_content")
        else:
            subject = raw_email.get("subject")
            html = raw_email.get("html_content")
            plain = raw_email.get("plain_text_content")
        if not all(isinstance(v, str) and v.strip() for v in (subject, html, plain)):
            continue
        templates.append(
            {
                "step_id": step_id,
                "subject": str(subject).strip(),
                "html_content": str(html).strip(),
                "plain_text_content": str(plain).strip(),
            },
        )
    return templates


def _strip_stale_artifacts(state: ConversationState, stage: str) -> None:
    """Remove workflow artifacts that cannot belong to the current approval stage."""
    if not state.get("brief_approved"):
        state["workflow"] = None
        state["email_templates"] = []
        return
    if stage in (ConversationStage.DISCOVERY, ConversationStage.CAMPAIGN_BRIEF):
        state["workflow"] = None
        state["email_templates"] = []
    elif stage == ConversationStage.WORKFLOW_GENERATION:
        state["email_templates"] = []


def normalize_conversation_state(state: ConversationState) -> ConversationState:
    """Recompute derived fields and drop artifacts that do not match the current stage."""
    normalized: ConversationState = deepcopy(state)
    if not normalized.get("brief_approved"):
        normalized["workflow"] = None
        normalized["email_templates"] = []

    normalized["missing_fields"] = compute_missing_fields(normalized)
    stage = resolve_stage(normalized)
    _strip_stale_artifacts(normalized, stage)
    normalized["current_stage"] = resolve_stage(normalized)
    normalized["missing_fields"] = compute_missing_fields(normalized)
    stage = normalized["current_stage"]

    workflow = normalized.get("workflow")
    if (
        isinstance(workflow, dict)
        and stage in STAGES_WITH_WORKFLOW_PREVIEW
        and isinstance(workflow.get("steps"), list)
    ):
        normalized["email_templates"] = email_templates_from_workflow(workflow)
    elif stage in (ConversationStage.DISCOVERY, ConversationStage.CAMPAIGN_BRIEF):
        normalized["email_templates"] = []

    recipients = normalized.get("recipients")
    if not isinstance(recipients, list):
        normalized["recipients"] = []

    thread_id = normalized.get("thread_id") or normalized.get("workflow_id")
    if thread_id:
        normalized["thread_id"] = str(thread_id)

    workflow_id = normalized.get("workflow_id")
    if workflow_id:
        normalized["campaign_id"] = str(normalized.get("campaign_id") or workflow_id)

    if not isinstance(normalized.get("leads"), dict):
        normalized["leads"] = {}
    if not isinstance(normalized.get("conversation_threads"), list):
        normalized["conversation_threads"] = []
    if not isinstance(normalized.get("tool_calls"), list):
        normalized["tool_calls"] = []
    if not isinstance(normalized.get("generated_responses"), list):
        normalized["generated_responses"] = []

    sync_approval_fields(normalized)

    return normalized


def sanitize_loaded_state(state: ConversationState) -> ConversationState:
    """Heal documents written before stage-aware previews (stale workflow on new campaigns)."""
    return normalize_conversation_state(state)


def should_expose_workflow_preview(state: ConversationState) -> bool:
    stage = resolve_stage_value(state)
    if stage not in STAGES_WITH_WORKFLOW_PREVIEW:
        return False
    workflow = state.get("workflow")
    return isinstance(workflow, dict) and isinstance(workflow.get("steps"), list) and bool(
        workflow.get("steps"),
    )


def should_expose_brief_preview(state: ConversationState) -> bool:
    stage = resolve_stage_value(state)
    if stage not in STAGES_WITH_BRIEF_PREVIEW:
        return False
    brief = state.get("campaign_brief")
    return isinstance(brief, dict) and bool(brief)
