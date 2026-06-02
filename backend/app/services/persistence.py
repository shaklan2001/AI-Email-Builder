from app.langgraph.state import ConversationState
from app.repositories.conversation_repository import conversation_repository
from app.repositories.email_template_repository import email_template_repository
from app.repositories.workflow_repository import workflow_repository
from app.services.conversation_state_service import (
    email_templates_from_workflow,
    normalize_conversation_state,
)


async def save_conversation_state(
    user_id: str,
    workflow_id: str,
    state: ConversationState,
) -> ConversationState:
    """Persist normalized conversation state and sync workflow definition when present."""
    normalized = normalize_conversation_state(state)
    await conversation_repository.upsert_conversation_state(
        user_id,
        workflow_id,
        normalized,
    )
    workflow = normalized.get("workflow")
    if isinstance(workflow, dict) and workflow.get("steps"):
        await workflow_repository.upsert_workflow_definition(
            user_id=user_id,
            workflow_id=workflow_id,
            workflow_definition=workflow,
        )
        templates = email_templates_from_workflow(workflow)
        if templates:
            await email_template_repository.sync_from_workflow(
                workflow_id=workflow_id,
                templates=templates,
            )
    else:
        await workflow_repository.clear_workflow_definition(
            user_id=user_id,
            workflow_id=workflow_id,
        )
    return normalized


async def save_campaign_state(
    user_id: str,
    workflow_id: str,
    state: ConversationState,
) -> ConversationState:
    return await save_conversation_state(user_id, workflow_id, state)
