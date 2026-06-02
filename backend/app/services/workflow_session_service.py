from dataclasses import dataclass

from app.langgraph.state import CampaignState
from app.repositories.conversation_repository import conversation_repository
from app.repositories.workflow_repository import workflow_repository
from app.schemas.requests import (
    CampaignBriefFieldData,
    CampaignDraftData,
    GeneratedEmailData,
    WorkflowDefinitionData,
    WorkflowSessionData,
)
from app.core.workflow_ids import assert_valid_workflow_id
from app.services.workflow_state_response import (
    brief_from_state,
    email_from_step_dict,
    workflow_from_state,
)


def empty_campaign_state(*, user_id: str, workflow_id: str) -> CampaignState:
    return CampaignState(
        workflow_id=workflow_id,
        user_id=user_id,
        messages=[],
        campaign_name=None,
        business_goal=None,
        product_info=None,
        audience=None,
        tone=None,
        cta=None,
        landing_page=None,
        product_image=None,
        brief_status=None,
        brief_approved=False,
        campaign_brief=None,
        workflow=None,
        skipped_fields=[],
    )


def _campaign_draft_from_state(state: CampaignState) -> CampaignDraftData:
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


def _generated_emails_from_state(state: CampaignState) -> list[GeneratedEmailData]:
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

        state = await conversation_repository.get_campaign_state(user_id, workflow_id)
        if state is None:
            return WorkflowSessionResult(
                session=WorkflowSessionData(
                    messages=[],
                    campaign_draft=CampaignDraftData(),
                    campaign_brief=None,
                    brief_status=None,
                    workflow=None,
                    generated_emails=[],
                ),
                found=True,
            )

        workflow_data = workflow_from_state(state)
        brief_data = brief_from_state(state)
        messages = list(state.get("messages") or [])

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
        await conversation_repository.upsert_campaign_state(
            user_id,
            workflow_id,
            empty_campaign_state(user_id=user_id, workflow_id=workflow_id),
        )


workflow_session_service = WorkflowSessionService()
