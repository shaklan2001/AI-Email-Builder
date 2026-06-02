from app.langgraph.state import CampaignState
from app.schemas.campaign_brief import CampaignBriefData
from app.schemas.email import GeneratedEmailContent
from app.schemas.requests import (
    CampaignBriefFieldData,
    EmailBodyVersionData,
    GeneratedEmailData,
    WorkflowDefinitionData,
    WorkflowStepData,
)


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


def brief_from_state(state: CampaignState) -> CampaignBriefFieldData | None:
    raw = state.get("campaign_brief")
    if not raw or not isinstance(raw, dict):
        return None
    try:
        brief = CampaignBriefData.model_validate(raw)
    except Exception:
        return None
    return CampaignBriefFieldData.model_validate(brief.to_api_dict())


def workflow_from_state(state: CampaignState) -> WorkflowDefinitionData | None:
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
    return WorkflowDefinitionData(
        workflow_type=workflow_type if isinstance(workflow_type, str) else None,
        steps=steps,
    )
