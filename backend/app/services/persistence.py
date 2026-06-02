from app.langgraph.state import CampaignState
from app.repositories.conversation_repository import conversation_repository
from app.repositories.workflow_repository import workflow_repository


async def save_campaign_state(
    user_id: str,
    workflow_id: str,
    state: CampaignState,
) -> None:
    await conversation_repository.upsert_campaign_state(user_id, workflow_id, state)
    workflow = state.get("workflow")
    if isinstance(workflow, dict):
        await workflow_repository.upsert_workflow_definition(
            user_id=user_id,
            workflow_id=workflow_id,
            workflow_definition=workflow,
        )
