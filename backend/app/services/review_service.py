"""Build workflow review payload and apply review-stage actions."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.langgraph.state import ConversationState
from app.repositories.lead_repository import lead_repository
from app.repositories.conversation_repository import conversation_repository
from app.repositories.workflow_repository import workflow_repository
from app.schemas.email import GeneratedEmailContent
from app.schemas.requests import ReviewData
from app.services.conversation_response import build_workflow_summary
from app.services.conversation_stage import _has_workflow_steps
from app.services.email_service import EmailService
from app.schemas.workflow import WorkflowDefinition


def _default_schedule() -> dict[str, str]:
    now = datetime.now(UTC)
    return {
        "startDate": now.strftime("%B %d, %Y"),
        "timezone": "UTC",
        "sendWindow": "Weekdays, 9:00 AM – 5:00 PM",
    }


def _workflow_summary_from_state(state: ConversationState) -> dict[str, object]:
    raw = state.get("workflow")
    if not isinstance(raw, dict):
        return {
            "name": state.get("campaign_name") or "Campaign Workflow",
            "description": "No workflow generated yet.",
            "steps": [],
        }
    try:
        definition = WorkflowDefinition.model_validate(raw)
    except Exception:
        return {
            "name": state.get("campaign_name") or "Campaign Workflow",
            "description": "Workflow definition unavailable.",
            "steps": [],
        }
    summary_text = build_workflow_summary(definition)
    lines = [line for line in summary_text.splitlines() if line.strip()]
    step_lines = [line for line in lines if not line.startswith("Workflow Summary") and line != "↓"]
    return {
        "name": state.get("campaign_name") or "Campaign Workflow",
        "description": "Generated outreach sequence from your campaign brief.",
        "steps": step_lines[:20],
    }


def _email_summary_from_state(state: ConversationState) -> dict[str, str]:
    raw = state.get("workflow")
    if not isinstance(raw, dict):
        return {"subject": "—", "bodyPreview": "No emails generated yet."}

    steps_raw = raw.get("steps")
    if not isinstance(steps_raw, list):
        return {"subject": "—", "bodyPreview": "No emails generated yet."}

    subjects: list[str] = []
    previews: list[str] = []
    for item in steps_raw:
        if not isinstance(item, dict) or item.get("type") != "send_email":
            continue
        raw_email = item.get("email")
        if not isinstance(raw_email, dict):
            continue
        try:
            parsed = GeneratedEmailContent.model_validate(raw_email)
            final = parsed.final_user_version
            subjects.append(final.subject)
            plain = final.plain_text_content.replace("\n", " ")
            previews.append(plain[:160] + ("…" if len(plain) > 160 else ""))
        except Exception:
            subject = raw_email.get("subject")
            plain = raw_email.get("plain_text_content")
            if isinstance(subject, str):
                subjects.append(subject)
            if isinstance(plain, str):
                previews.append(plain[:160])

    if not subjects:
        return {"subject": "—", "bodyPreview": "No emails generated yet."}

    return {
        "subject": subjects[0] if len(subjects) == 1 else f"{subjects[0]} (+{len(subjects) - 1} more)",
        "bodyPreview": previews[0] if previews else "",
    }


def _recipient_count_from_state(state: ConversationState) -> int:
    raw = state.get("workflow")
    if isinstance(raw, dict):
        recipients = EmailService._extract_recipients(raw)
        if recipients:
            return len(recipients)
    stored = state.get("recipients")
    if isinstance(stored, list):
        return len(stored)
    return 0


def build_review_data(
    state: ConversationState,
    *,
    lead_status_counts: dict[str, int] | None = None,
) -> ReviewData:
    return ReviewData(
        workflow_summary=_workflow_summary_from_state(state),
        email_summary=_email_summary_from_state(state),
        recipient_count=_recipient_count_from_state(state),
        schedule_summary=_default_schedule(),
        review_status=str(state.get("review_status") or "pending"),
        activation_allowed=state.get("review_status") == "approved",
        lead_status_counts=lead_status_counts or {},
    )


def apply_review_approve(state: ConversationState) -> dict[str, object]:
    if not _has_workflow_steps(state.get("workflow")):
        return {
            "assistant_reply": (
                "Your workflow is not ready for approval yet. "
                "Finish generating the workflow and emails first."
            ),
        }
    return {
        "review_status": "approved",
        "assistant_reply": (
            "Your workflow is approved. You can activate the campaign when recipients are ready."
        ),
    }


def apply_review_edit_campaign(state: ConversationState) -> dict[str, object]:
    return {
        "review_status": "editing",
        "brief_approved": False,
        "brief_status": "editing",
        "campaign_brief": None,
        "assistant_reply": (
            "No problem — tell me what you'd like to change about your campaign "
            "and I'll update the brief."
        ),
    }


def apply_review_regenerate_workflow(state: ConversationState) -> dict[str, object]:
    if not state.get("brief_approved"):
        return {
            "assistant_reply": (
                "Approve your campaign brief first, then you can regenerate the workflow."
            ),
        }
    return {
        "workflow": None,
        "email_templates": [],
        "review_status": "pending",
        "regenerate_workflow": True,
        "assistant_reply": (
            "I'll regenerate your workflow and emails from the approved campaign brief. "
            "This may take a moment."
        ),
    }


class ReviewService:
    async def get_review(self, *, user_id: str, workflow_id: str) -> ReviewData:
        state = await conversation_repository.get_conversation_state(user_id, workflow_id)
        if state is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )
        if not _has_workflow_steps(state.get("workflow")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow is not ready for review",
            )
        return build_review_data(
            state,
            lead_status_counts=await lead_repository.count_by_status(workflow_id),
        )

    async def approve(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> ReviewData:
        state = await conversation_repository.get_conversation_state(user_id, workflow_id)
        if state is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )
        updates = apply_review_approve(state)
        if updates.get("review_status") != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(updates.get("assistant_reply", "Cannot approve workflow")),
            )
        merged: ConversationState = {**state, **updates}  # type: ignore[misc]
        from app.services.persistence import save_conversation_state

        saved = await save_conversation_state(user_id, workflow_id, merged)
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is not None and record.status == "draft":
            await workflow_repository.update_status(
                user_id=user_id,
                workflow_id=workflow_id,
                status="awaiting_activation",
            )
        return build_review_data(
            saved,
            lead_status_counts=await lead_repository.count_by_status(workflow_id),
        )


review_service = ReviewService()
