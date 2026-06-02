from fastapi import HTTPException, status

from app.schemas.email import EmailBodyVersion, GeneratedEmailContent
from app.schemas.requests import UpdateWorkflowEmailRequest, WorkflowDefinitionData
from app.services.workflow_state_response import workflow_from_state
from app.repositories.conversation_repository import conversation_repository
from app.services.persistence import save_campaign_state


class WorkflowEmailService:
    async def update_step_email(
        self,
        *,
        user_id: str,
        workflow_id: str,
        step_id: str,
        body: UpdateWorkflowEmailRequest,
    ) -> WorkflowDefinitionData:
        state = await conversation_repository.get_campaign_state(user_id, workflow_id)
        if state is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow conversation not found",
            )

        raw_workflow = state.get("workflow")
        if not raw_workflow or not isinstance(raw_workflow, dict):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        steps_raw = raw_workflow.get("steps")
        if not isinstance(steps_raw, list):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow steps not found",
            )

        step_found = False
        updated_steps: list[dict[str, object]] = []
        for item in steps_raw:
            if not isinstance(item, dict):
                continue
            if item.get("id") != step_id:
                updated_steps.append(item)
                continue

            if item.get("type") != "send_email":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Step is not a send_email step",
                )

            step_found = True
            raw_email = item.get("email")
            if isinstance(raw_email, dict):
                try:
                    existing = GeneratedEmailContent.model_validate(raw_email)
                except Exception:
                    existing = GeneratedEmailContent.from_ai_draft(
                        subject=body.subject,
                        html_content=body.html_content,
                        plain_text_content=body.plain_text_content,
                    )
            else:
                existing = GeneratedEmailContent.from_ai_draft(
                    subject=body.subject,
                    html_content=body.html_content,
                    plain_text_content=body.plain_text_content,
                )

            final = EmailBodyVersion(
                subject=body.subject.strip(),
                html_content=body.html_content.strip(),
                plain_text_content=body.plain_text_content.strip(),
            )
            updated_email = existing.model_copy(
                update={"final_user_version": final, "user_edited": True},
            )
            updated_item = {**item, "email": updated_email.to_api_dict()}
            updated_steps.append(updated_item)

        if not step_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow step not found",
            )

        raw_workflow["steps"] = updated_steps
        state["workflow"] = raw_workflow
        await save_campaign_state(user_id, workflow_id, state)

        workflow_data = workflow_from_state(state)
        if workflow_data is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load updated workflow",
            )
        return workflow_data


workflow_email_service = WorkflowEmailService()
