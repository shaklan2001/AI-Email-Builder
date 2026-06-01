from app.agents.copywriter_agent import copywriter_agent
from app.agents.workflow_agent import workflow_agent
from app.langgraph.state import CampaignState, apply_campaign_data, campaign_data_from_state
from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.repositories.workflow_repository import workflow_repository
from app.services.campaign_extraction import extract_from_latest_user_message
from app.services.campaign_field_policy import (
    apply_field_defaults,
    infer_product_from_minimal_message,
    is_proceed_message,
    is_skip_message,
    mark_all_optional_skipped,
    next_field_to_collect,
    normalize_skipped_fields,
    resolve_skip_for_field,
)
from app.services.campaign_revision import (
    campaign_changed,
    is_material_change,
    is_revision_message,
    stale_artifact_reset,
)
from app.services.campaign_state import campaign_for_generation
from app.services.conversation_response import (
    build_brief_approval_reply,
    build_brief_update_reply,
    build_campaign_brief,
    build_collection_reply,
    detect_brief_changes,
    build_post_generation_reply,
    build_product_required_after_skip,
)

_POST_GENERATION_SYSTEM = """You are a sales campaign strategist. The user's workflow and emails are already built.
Answer in one or two short sentences. Help with review, workflow changes, or activation.
Never tell the user to manually add blocks, CTAs, images, or workflow steps — you are the builder.
Never regenerate the full workflow unless asked."""


def _get_llm() -> LLMProvider:
    return get_groq_provider()


def _has_workflow_steps(raw_workflow: object) -> bool:
    return (
        isinstance(raw_workflow, dict)
        and isinstance(raw_workflow.get("steps"), list)
        and len(raw_workflow["steps"]) > 0
    )


def _is_post_generation_mode(state: CampaignState) -> bool:
    """True only after the user approved the brief and a workflow was generated."""
    return bool(state.get("brief_approved")) and _has_workflow_steps(state.get("workflow"))


def _latest_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "").strip()
    return ""


async def extract_information_node(state: CampaignState) -> dict[str, object]:
    llm = _get_llm()
    before = campaign_data_from_state(state)
    messages = list(state.get("messages") or [])
    latest = _latest_user_message(messages)
    revision = is_revision_message(latest)
    skipped = normalize_skipped_fields(state.get("skipped_fields"))
    editing_brief = state.get("brief_status") == "editing"

    current = extract_from_latest_user_message(messages, before, revision=revision)
    extracted = await llm.extract_campaign_data(messages, current, revision=revision)
    merged = extract_from_latest_user_message(messages, extracted, revision=revision)

    minimal_product = infer_product_from_minimal_message(latest)
    if minimal_product and not merged.product_info:
        merged = merged.apply_updates({"product_info": minimal_product})

    next_ask = next_field_to_collect(
        merged,
        skipped,
        include_optional=editing_brief,
    )
    if is_skip_message(latest) and next_ask and next_ask != "product_info":
        skipped, patches = resolve_skip_for_field(next_ask, skipped)
        merged = merged.apply_updates(patches)
    elif is_skip_message(latest) or is_proceed_message(latest):
        skipped = mark_all_optional_skipped(skipped)

    merged = apply_field_defaults(merged, skipped)

    updates = apply_campaign_data(state, merged)
    updates["skipped_fields"] = sorted(skipped)
    if merged.campaign_name:
        updates["campaign_name"] = merged.campaign_name
        workflow_id = state.get("workflow_id") or ""
        user_id = state.get("user_id") or ""
        if workflow_id and user_id:
            await workflow_repository.update_name(
                user_id=user_id,
                workflow_id=workflow_id,
                name=merged.campaign_name,
            )

    if campaign_changed(before, merged) and (
        revision or is_material_change(before, merged) or state.get("brief_approved")
    ):
        updates.update(stale_artifact_reset(clear_brief=revision or is_material_change(before, merged)))

    if not state.get("brief_approved") and "workflow" not in updates:
        updates["workflow"] = None
    return updates


async def missing_information_node(state: CampaignState) -> dict[str, object]:
    campaign = campaign_data_from_state(state)
    return {"missing_fields": campaign.missing_fields()}


async def question_generator_node(state: CampaignState) -> dict[str, object]:
    campaign = campaign_data_from_state(state)
    messages = list(state.get("messages") or [])

    if _is_post_generation_mode(state):
        llm = _get_llm()
        user_prompt = (
            "The campaign workflow and emails are already generated. "
            "Recent conversation:\n"
            + "\n".join(f"{m['role']}: {m['content']}" for m in messages[-6:])
        )
        try:
            reply = await llm.generate(_POST_GENERATION_SYSTEM, user_prompt)
        except LLMProviderError as exc:
            raise exc
        return {"assistant_reply": reply}

    editing_brief = state.get("brief_status") == "editing"
    skipped = normalize_skipped_fields(state.get("skipped_fields"))
    campaign = apply_field_defaults(campaign, skipped)
    latest = _latest_user_message(messages)

    if is_skip_message(latest) and not campaign.product_info:
        reply = build_product_required_after_skip()
    else:
        reply = build_collection_reply(
            campaign,
            editing_brief=editing_brief,
            skipped_fields=skipped,
        )
    return {"assistant_reply": reply}


async def generate_workflow_node(state: CampaignState) -> dict[str, object]:
    campaign = campaign_for_generation(state)

    try:
        definition, _reply = await workflow_agent.generate_workflow(campaign)
    except LLMProviderError as exc:
        raise exc

    return {
        "workflow": definition.to_api_dict(),
        "assistant_reply": "",
    }


async def generate_emails_node(state: CampaignState) -> dict[str, object]:
    campaign = campaign_for_generation(state)
    raw_workflow = state.get("workflow")
    if not raw_workflow or not isinstance(raw_workflow, dict):
        return {}

    steps_raw = raw_workflow.get("steps")
    if not isinstance(steps_raw, list):
        return {}

    steps: list[WorkflowStep] = []
    for item in steps_raw:
        if isinstance(item, dict):
            try:
                steps.append(WorkflowStep.model_validate(item))
            except Exception:
                continue

    if not steps:
        return {}

    definition = WorkflowDefinition(
        workflow_type=raw_workflow.get("workflow_type")
        if raw_workflow.get("workflow_type")
        in ("linear", "conditional", "multi_level_conditional")
        else None,
        steps=steps,
    )

    try:
        with_emails = await copywriter_agent.generate_emails_for_workflow(campaign, definition)
    except LLMProviderError as exc:
        raise exc

    email_count = sum(1 for s in with_emails.steps if s.type == "send_email" and s.email)
    assistant_reply = build_post_generation_reply(with_emails, email_count=email_count)

    return {
        "workflow": with_emails.to_api_dict(),
        "assistant_reply": assistant_reply,
    }


async def campaign_brief_node(state: CampaignState) -> dict[str, object]:
    skipped = normalize_skipped_fields(state.get("skipped_fields"))
    campaign = apply_field_defaults(campaign_data_from_state(state), skipped)
    messages = list(state.get("messages") or [])
    workflow_id = state.get("workflow_id") or ""
    user_id = state.get("user_id") or ""

    campaign_name = campaign.campaign_name or state.get("campaign_name")
    if workflow_id and user_id:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if campaign_name:
            await workflow_repository.update_name(
                user_id=user_id,
                workflow_id=workflow_id,
                name=campaign_name,
            )
        elif record is not None:
            campaign_name = record.name

    attachments = state.get("attachments")
    product_image = campaign.product_image or state.get("product_image")
    landing_page = campaign.landing_page or state.get("landing_page")

    brief = build_campaign_brief(
        campaign,
        campaign_name=campaign_name,
        messages=messages,
        attachments=attachments,
        landing_page=landing_page,
        follow_up_strategy=state.get("follow_up_strategy"),
        reply_strategy=state.get("reply_strategy"),
        state_only=True,
    )

    previous_brief = state.get("campaign_brief")
    changes = (
        detect_brief_changes(previous_brief, brief)
        if isinstance(previous_brief, dict)
        else []
    )
    if isinstance(previous_brief, dict) and changes:
        reply = build_brief_update_reply(changes)
    else:
        reply = build_brief_approval_reply(campaign)

    return {
        "campaign_brief": brief.to_api_dict(),
        "brief_status": "pending_approval",
        "brief_approved": False,
        "campaign_name": campaign_name,
        "follow_up_strategy": brief.follow_up_strategy,
        "reply_strategy": brief.reply_strategy,
        "attachments": brief.attachments,
        "landing_page": brief.landing_page,
        "product_image": product_image,
        "assistant_reply": reply,
    }


def route_after_missing_information(state: CampaignState) -> str:
    if state.get("brief_approved"):
        return "generate_workflow"

    campaign = campaign_data_from_state(state)
    if not campaign.has_required_for_workflow():
        return "question_generator"

    if state.get("brief_status") == "editing":
        return "question_generator"

    if state.get("brief_status") == "pending_approval":
        return "campaign_brief"

    return "campaign_brief"
