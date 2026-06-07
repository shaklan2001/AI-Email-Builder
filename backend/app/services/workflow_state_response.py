from app.langgraph.state import ConversationState, campaign_data_from_state
from app.services.conversation_state_service import (
    should_expose_brief_preview,
    should_expose_workflow_preview,
)
from app.schemas.campaign_brief import CampaignBriefData
from app.schemas.conversation_stage import ConversationStage
from app.schemas.email import GeneratedEmailContent
from app.schemas.follow_up_delay import FollowUpDelay
from app.schemas.requests import (
    CampaignBriefFieldData,
    EmailBodyVersionData,
    FollowUpDelayData,
    GeneratedEmailData,
    WorkflowDefinitionData,
    WorkflowStepData,
)
from app.services.campaign_field_policy import has_email_length, has_wants_follow_up, normalize_skipped_fields, resolve_wants_cta
from app.services.conversation_response import build_campaign_brief
from app.services.conversation_stage import resolve_stage_value


def _version_from_dict(raw: dict[str, object]) -> EmailBodyVersionData | None:
    subject = raw.get("subject")
    html = raw.get("html_content")
    plain = raw.get("plain_text_content")
    if not all(isinstance(v, str) and v.strip() for v in (subject, html, plain)):
        return None
    return EmailBodyVersionData(
        subject=str(subject).strip(),
        html_content=str(html).strip(),
        plain_text_content=str(plain).strip(),
    )


def email_from_step_dict(item: dict[str, object]) -> GeneratedEmailData | None:
    raw_email = item.get("email")
    if not isinstance(raw_email, dict):
        return None

    try:
        parsed = GeneratedEmailContent.model_validate(raw_email)
        final = parsed.final_user_version
        ai = parsed.ai_generated_version
        return GeneratedEmailData(
            subject=final.subject,
            html_content=final.html_content,
            plain_text_content=final.plain_text_content,
            ai_generated_version=EmailBodyVersionData(
                subject=ai.subject,
                html_content=ai.html_content,
                plain_text_content=ai.plain_text_content,
            ),
            final_user_version=EmailBodyVersionData(
                subject=final.subject,
                html_content=final.html_content,
                plain_text_content=final.plain_text_content,
            ),
            user_edited=parsed.user_edited,
        )
    except Exception:
        subject = raw_email.get("subject")
        html = raw_email.get("html_content")
        plain = raw_email.get("plain_text_content")
        if not all(isinstance(v, str) and v.strip() for v in (subject, html, plain)):
            return None
        body = EmailBodyVersionData(
            subject=str(subject).strip(),
            html_content=str(html).strip(),
            plain_text_content=str(plain).strip(),
        )
        return GeneratedEmailData(
            subject=body.subject,
            html_content=body.html_content,
            plain_text_content=body.plain_text_content,
            ai_generated_version=body,
            final_user_version=body,
            user_edited=bool(raw_email.get("user_edited", False)),
        )


def _draft_brief_from_state(state: ConversationState) -> CampaignBriefFieldData | None:
    """Live preview while discovery is still in progress."""
    if resolve_stage_value(state) != ConversationStage.DISCOVERY:
        return None
    if state.get("brief_status") in ("pending_approval", "approved", "editing"):
        return None

    campaign = campaign_data_from_state(state)
    if not campaign.product_info:
        return None
    if not has_email_length(state.get("email_length")):
        return None
    if not has_wants_follow_up(state.get("wants_follow_up")):
        return None

    campaign_name = state.get("campaign_name")
    skipped = normalize_skipped_fields(state.get("skipped_fields"))
    wants_cta = resolve_wants_cta(state.get("wants_cta"), skipped)
    brief = build_campaign_brief(
        campaign,
        campaign_name=campaign_name if isinstance(campaign_name, str) else None,
        messages=list(state.get("messages") or []),
        product_image=state.get("product_image") if isinstance(state.get("product_image"), str) else None,
        landing_page=state.get("landing_page") if isinstance(state.get("landing_page"), str) else None,
        follow_up_delay=state.get("follow_up_delay"),
        wants_follow_up=state.get("wants_follow_up") if isinstance(state.get("wants_follow_up"), bool) else None,
        wants_cta=wants_cta,
        email_length=state.get("email_length") if isinstance(state.get("email_length"), str) else None,
        email_length_words=state.get("email_length_words") if isinstance(state.get("email_length_words"), int) else None,
        reply_handling=state.get("reply_strategy") if isinstance(state.get("reply_strategy"), str) else None,
        skipped_fields=skipped,
    )
    return CampaignBriefFieldData.model_validate(brief.to_api_dict())


def brief_from_state(state: ConversationState) -> CampaignBriefFieldData | None:
    if should_expose_brief_preview(state):
        raw = state.get("campaign_brief")
        if not raw or not isinstance(raw, dict):
            return None
        try:
            brief = CampaignBriefData.model_validate(raw)
        except Exception:
            return None
        return CampaignBriefFieldData.model_validate(brief.to_api_dict())

    return _draft_brief_from_state(state)


def workflow_from_state(state: ConversationState) -> WorkflowDefinitionData | None:
    if not should_expose_workflow_preview(state):
        return None
    raw = state.get("workflow")
    if not raw or not isinstance(raw, dict):
        return None

    steps_raw = raw.get("steps")
    if not isinstance(steps_raw, list):
        return None

    steps: list[WorkflowStepData] = []
    for item in steps_raw:
        if not isinstance(item, dict):
            continue
        step_id = item.get("id")
        step_type = item.get("type")
        if not isinstance(step_id, str) or not isinstance(step_type, str):
            continue
        email_data = email_from_step_dict(item)
        steps.append(
            WorkflowStepData(
                id=step_id,
                type=step_type,
                name=item.get("name") if isinstance(item.get("name"), str) else None,
                days=item.get("days") if isinstance(item.get("days"), int) else None,
                value=item.get("value") if isinstance(item.get("value"), int) else None,
                unit=item.get("unit") if isinstance(item.get("unit"), str) else None,
                condition=item.get("condition")
                if isinstance(item.get("condition"), str)
                else None,
                branch=item.get("branch") if isinstance(item.get("branch"), str) else None,
                email=email_data,
            )
        )

    if not steps:
        return None

    workflow_type = raw.get("workflow_type")
    delay_raw = raw.get("follow_up_delay")
    follow_up_delay: FollowUpDelayData | None = None
    if isinstance(delay_raw, dict):
        try:
            parsed_delay = FollowUpDelay.model_validate(delay_raw)
            follow_up_delay = FollowUpDelayData(
                value=parsed_delay.value,
                unit=parsed_delay.unit,
            )
        except Exception:
            follow_up_delay = None

    return WorkflowDefinitionData(
        workflow_type=workflow_type if isinstance(workflow_type, str) else None,
        follow_up_delay=follow_up_delay,
        steps=steps,
    )
