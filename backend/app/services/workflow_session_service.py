from dataclasses import dataclass

from app.langgraph.state import ConversationState
from app.repositories.conversation_repository import conversation_repository
from app.repositories.workflow_repository import workflow_repository
from app.schemas.requests import (
    CampaignBriefFieldData,
    CampaignDraftData,
    GeneratedEmailData,
    RecipientCountsData,
    RecipientItemData,
    WorkflowDefinitionData,
    WorkflowSessionData,
)
from app.services.recipient_service import _emails_from_state_recipients
from app.services.email_service import EmailService
from app.core.workflow_ids import assert_valid_workflow_id
from app.services.conversation_state_service import empty_conversation_state
from app.services.persistence import save_conversation_state
from app.services.workflow_state_response import (
    brief_from_state,
    email_from_step_dict,
    workflow_from_state,
)


def empty_campaign_state(*, user_id: str, workflow_id: str) -> ConversationState:
    return empty_conversation_state(user_id=user_id, workflow_id=workflow_id)


def _campaign_draft_from_state(state: ConversationState) -> CampaignDraftData:
    return CampaignDraftData(
        campaign_name=state.get("campaign_name"),
        business_goal=state.get("business_goal"),
        product_info=state.get("product_info"),
        audience=state.get("audience"),
        tone=state.get("tone"),
        cta=state.get("cta"),
        landing_page=state.get("landing_page"),
        product_image=state.get("product_image"),
        follow_up_strategy=state.get("follow_up_strategy"),
        reply_strategy=state.get("reply_strategy"),
    )


def _generated_emails_from_state(state: ConversationState) -> list[GeneratedEmailData]:
    raw = state.get("workflow")
    if not raw or not isinstance(raw, dict):
        return []

    steps_raw = raw.get("steps")
    if not isinstance(steps_raw, list):
        return []

    emails: list[GeneratedEmailData] = []
    for item in steps_raw:
        if not isinstance(item, dict) or item.get("type") != "send_email":
            continue
        email_data = email_from_step_dict(item)
        if email_data is not None:
            emails.append(email_data)
    return emails


@dataclass
class WorkflowSessionResult:
    session: WorkflowSessionData
    found: bool


class WorkflowSessionService:
    async def get_session(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> WorkflowSessionResult | None:
        assert_valid_workflow_id(workflow_id)
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is None:
            return None

        state = await conversation_repository.get_conversation_state(user_id, workflow_id)
        if state is None:
            return WorkflowSessionResult(
                session=WorkflowSessionData(
                    messages=[],
                    campaign_draft=CampaignDraftData(),
                    campaign_brief=None,
                    brief_status=None,
                    workflow=None,
                    generated_emails=[],
                    recipients=[],
                    recipient_counts=RecipientCountsData(validCount=0, invalidCount=0),
                ),
                found=True,
            )

        workflow_data = workflow_from_state(state)
        brief_data = brief_from_state(state)
        messages = list(state.get("messages") or [])

        recipient_emails = _emails_from_state_recipients(state.get("recipients"))
        workflow_raw = state.get("workflow")
        if isinstance(workflow_raw, dict):
            recipient_emails = list(
                dict.fromkeys(
                    [
                        *recipient_emails,
                        *EmailService._extract_recipients(workflow_raw),
                    ],
                ),
            )
        if (
            not recipient_emails
            and record.workflow_definition
            and isinstance(record.workflow_definition, dict)
        ):
            recipient_emails = EmailService._extract_recipients(record.workflow_definition)

        recipient_items = [
            RecipientItemData(email=email)
            for email in recipient_emails
        ]

        return WorkflowSessionResult(
            session=WorkflowSessionData(
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in messages
                    if isinstance(m, dict)
                    and isinstance(m.get("role"), str)
                    and isinstance(m.get("content"), str)
                ],
                campaign_draft=_campaign_draft_from_state(state),
                campaign_brief=brief_data,
                brief_status=state.get("brief_status"),
                workflow=workflow_data,
                generated_emails=_generated_emails_from_state(state),
                recipients=recipient_items,
                recipient_counts=RecipientCountsData(
                    validCount=len(recipient_emails),
                    invalidCount=0,
                ),
            ),
            found=True,
        )

    async def initialize_empty_session(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> None:
        assert_valid_workflow_id(workflow_id)
        await save_conversation_state(
            user_id,
            workflow_id,
            empty_campaign_state(user_id=user_id, workflow_id=workflow_id),
        )


workflow_session_service = WorkflowSessionService()
