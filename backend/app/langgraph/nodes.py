from app.agents.campaign_collection_agent import campaign_collection_agent
from app.agents.email_generation_agent import email_generation_agent
from app.agents.workflow_agent import workflow_agent
from app.langgraph.state import CampaignState, campaign_data_from_state
from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.repositories.workflow_repository import workflow_repository
from app.services.campaign_field_policy import (
    apply_field_defaults,
    next_field_to_collect,
    normalize_skipped_fields,
    resolve_wants_cta,
)
from app.services.campaign_naming import is_placeholder_campaign_name
from app.services.follow_up_delay import (
    follow_up_delay_from_state,
    format_follow_up_strategy,
)
from app.services.campaign_state import campaign_for_generation
from app.services.conversation_response import (
    POST_GENERATION_REPLY_SYSTEM,
    build_campaign_brief,
    build_post_generation_prompt_context,
    detect_brief_changes,
    build_post_generation_reply,
)
from app.services.follow_up_delay import is_affirmation_message
from app.services.workflow_modification import (
    apply_post_generation_workflow_edit,
    follow_up_email_needs_generation,
)


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


async def _generate_missing_follow_up_email(
    state: CampaignState,
    updates: dict[str, object],
) -> dict[str, object]:
    """Generate copy for a newly added follow-up step when no draft exists."""
    raw_workflow = updates.get("workflow")
    if not isinstance(raw_workflow, dict):
        return updates

    try:
        definition = WorkflowDefinition.model_validate(raw_workflow)
    except Exception:
        return updates

    if not follow_up_email_needs_generation(definition):
        return updates

    follow_up_step = next(
        (s for s in reversed(definition.steps) if s.type == "send_email"),
        None,
    )
    if follow_up_step is None:
        return updates

    campaign = campaign_for_generation(state)
    email_steps = [s for s in definition.steps if s.type == "send_email"]
    try:
        content = await email_generation_agent.generate_email_for_step(
            campaign=campaign,
            step=follow_up_step,
            steps=definition.steps,
            step_index=max(len(email_steps) - 1, 0),
            total_email_steps=len(email_steps),
            email_length=state.get("email_length"),
            email_length_words=state.get("email_length_words"),
        )
    except LLMProviderError:
        return updates

    patched_steps: list[WorkflowStep] = []
    for step in definition.steps:
        if step.id == follow_up_step.id:
            patched_steps.append(step.model_copy(update={"email": content}))
        else:
            patched_steps.append(step)

    updated_definition = definition.model_copy(update={"steps": patched_steps})
    return {
        **updates,
        "workflow": updated_definition.to_api_dict(),
    }


async def extract_information_node(state: CampaignState) -> dict[str, object]:
    try:
        return await campaign_collection_agent.extract_and_update(state)
    except LLMProviderError as exc:
        raise exc


async def missing_information_node(state: CampaignState) -> dict[str, object]:
    return campaign_collection_agent.missing_fields_snapshot(state)


async def question_generator_node(state: CampaignState) -> dict[str, object]:
    messages = list(state.get("messages") or [])

    if _is_post_generation_mode(state):
        latest = _latest_user_message(messages)
        if is_affirmation_message(latest):
            return {
                "assistant_reply": (
                    "Glad those work for you! Check the Emails tab to review each draft, "
                    "or tell me if you'd like any changes."
                ),
            }

        workflow_edit = apply_post_generation_workflow_edit(state, latest)
        if workflow_edit is not None:
            if workflow_edit.pop("_generate_follow_up_email", False):
                workflow_edit = await _generate_missing_follow_up_email(state, workflow_edit)
            return workflow_edit

        llm = _get_llm()
        user_prompt = build_post_generation_prompt_context(state, messages)
        try:
            reply = await llm.generate(POST_GENERATION_REPLY_SYSTEM, user_prompt)
        except LLMProviderError as exc:
            raise exc
        return {"assistant_reply": reply}

    try:
        reply = await campaign_collection_agent.build_next_question(state)
    except LLMProviderError as exc:
        raise exc
    return {"assistant_reply": reply}


async def generate_workflow_node(state: CampaignState) -> dict[str, object]:
    campaign = campaign_for_generation(state)
    wants_follow_up = state.get("wants_follow_up")
    if wants_follow_up is None:
        return {}

    delay = follow_up_delay_from_state(state.get("follow_up_delay"))
    if wants_follow_up and delay is None:
        return {}

    name_updates = await campaign_collection_agent.ensure_workflow_display_name(state, campaign)

    try:
        definition, _reply = await workflow_agent.generate_workflow(
            campaign,
            follow_up_delay=delay,
            wants_follow_up=bool(wants_follow_up),
        )
    except LLMProviderError as exc:
        raise exc

    return {
        **name_updates,
        "workflow": definition.to_api_dict(),
        "review_status": None,
        "regenerate_workflow": False,
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
        workflow_id = state.get("workflow_id") or ""
        with_emails = await email_generation_agent.generate_emails_for_workflow(
            campaign,
            definition,
            workflow_id=workflow_id or None,
            persist=bool(workflow_id),
            email_length=state.get("email_length"),
            email_length_words=state.get("email_length_words"),
        )
    except LLMProviderError as exc:
        raise exc

    email_count = sum(1 for s in with_emails.steps if s.type == "send_email" and s.email)
    assistant_reply = build_post_generation_reply(with_emails, email_count=email_count)

    return {
        "workflow": with_emails.to_api_dict(),
        "review_status": "pending",
        "regenerate_workflow": False,
        "assistant_reply": assistant_reply,
    }


async def campaign_brief_node(state: CampaignState) -> dict[str, object]:
    skipped = normalize_skipped_fields(state.get("skipped_fields"))
    campaign = apply_field_defaults(campaign_data_from_state(state), skipped, wants_cta=state.get("wants_cta"))
    messages = list(state.get("messages") or [])
    workflow_id = state.get("workflow_id") or ""
    user_id = state.get("user_id") or ""

    campaign_name = campaign.campaign_name or state.get("campaign_name")
    if isinstance(campaign_name, str):
        campaign_name = campaign_name.strip() or None
    if workflow_id and user_id:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if campaign_name:
            await workflow_repository.update_name(
                user_id=user_id,
                workflow_id=workflow_id,
                name=campaign_name,
            )
        elif record is not None and not is_placeholder_campaign_name(record.name):
            campaign_name = record.name

    product_image = campaign.product_image or state.get("product_image")
    landing_page = campaign.landing_page or state.get("landing_page")

    brief = build_campaign_brief(
        campaign,
        campaign_name=campaign_name,
        messages=messages,
        product_image=product_image,
        landing_page=landing_page,
        follow_up_delay=state.get("follow_up_delay"),
        wants_follow_up=state.get("wants_follow_up"),
        wants_cta=resolve_wants_cta(state.get("wants_cta"), skipped),
        email_length=state.get("email_length"),
        email_length_words=state.get("email_length_words"),
        reply_handling=state.get("reply_strategy"),
        skipped_fields=skipped,
        state_only=True,
    )

    previous_brief = state.get("campaign_brief")
    changes = (
        detect_brief_changes(previous_brief, brief)
        if isinstance(previous_brief, dict)
        else []
    )
    reply = await campaign_collection_agent.build_brief_reply(
        state,
        changes=changes if isinstance(previous_brief, dict) and changes else None,
    )

    return {
        "campaign_brief": brief.to_api_dict(),
        "brief_status": "pending_approval",
        "brief_approved": False,
        "campaign_name": campaign_name,
        "follow_up_strategy": (
            format_follow_up_strategy(delay)
            if state.get("wants_follow_up")
            and (delay := follow_up_delay_from_state(state.get("follow_up_delay")))
            is not None
            else (
                "No follow-up — initial email only"
                if state.get("wants_follow_up") is False
                else None
            )
        ),
        "follow_up_delay": state.get("follow_up_delay"),
        "reply_strategy": brief.reply_handling,
        "landing_page": brief.landing_page,
        "product_image": product_image,
        "assistant_reply": reply,
    }


def route_after_missing_information(state: CampaignState) -> str:
    if state.get("regenerate_workflow"):
        return "generate_workflow"

    workflow = state.get("workflow")
    if state.get("brief_approved") and not _has_workflow_steps(workflow):
        return "generate_workflow"

    if _is_post_generation_mode(state):
        return "question_generator"

    campaign = campaign_data_from_state(state)
    if not campaign.has_required_for_workflow_with_delay(
        state.get("follow_up_delay"),
        wants_follow_up=state.get("wants_follow_up"),
        email_length=state.get("email_length"),
    ):
        return "question_generator"

    skipped = normalize_skipped_fields(state.get("skipped_fields"))
    resolved_campaign = apply_field_defaults(
        campaign,
        skipped,
        wants_cta=state.get("wants_cta"),
    )
    raw_messages = state.get("messages")
    messages = raw_messages if isinstance(raw_messages, list) else None
    if next_field_to_collect(
        resolved_campaign,
        skipped,
        include_optional=state.get("brief_status") == "editing",
        follow_up_delay=state.get("follow_up_delay"),
        wants_follow_up=state.get("wants_follow_up"),
        wants_cta=state.get("wants_cta"),
        email_length=state.get("email_length"),
        messages=messages,
    ):
        return "question_generator"

    if state.get("brief_status") == "editing":
        return "question_generator"

    if state.get("brief_status") == "pending_approval":
        return "campaign_brief"

    return "campaign_brief"
