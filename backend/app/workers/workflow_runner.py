from fastapi import HTTPException

from app.repositories.conversation_repository import conversation_repository
from app.repositories.workflow_repository import workflow_repository
from app.repositories.workflow_run_repository import workflow_run_repository
from app.schemas.workflow import StepType, WorkflowDefinition
from app.services.workflow_execution_service import (
    StepExecutionResult,
    WorkflowExecutionService,
    workflow_execution_service,
)
from app.workers.dispatch import dispatch_after_step, enqueue_send_email


async def _load_workflow_definition(
    *,
    user_id: str,
    workflow_id: str,
) -> WorkflowDefinition:
    record = await workflow_repository.get_by_id(user_id, workflow_id)
    if record is not None and isinstance(record.workflow_definition, dict):
        return WorkflowDefinition.model_validate(record.workflow_definition)

    state = await conversation_repository.get_campaign_state(user_id, workflow_id)
    if state is not None:
        raw_workflow = state.get("workflow")
        if isinstance(raw_workflow, dict):
            return WorkflowDefinition.model_validate(raw_workflow)

    raise HTTPException(status_code=404, detail="Workflow not found")


async def _current_step_type(
    *,
    user_id: str,
    workflow_run_id: str,
) -> StepType | None:
    run = await workflow_run_repository.get_by_id(workflow_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    definition = await _load_workflow_definition(user_id=user_id, workflow_id=run.workflow_id)
    for step in definition.steps:
        if step.id == run.current_step:
            return step.type
    return None


async def run_execute_workflow_step(
    *,
    user_id: str,
    workflow_run_id: str,
    service: WorkflowExecutionService | None = None,
) -> StepExecutionResult | None:
    execution = service or workflow_execution_service
    step_type = await _current_step_type(
        user_id=user_id,
        workflow_run_id=workflow_run_id,
    )
    if step_type == "send_email":
        enqueue_send_email(user_id=user_id, workflow_run_id=workflow_run_id)
        return None

    result = await execution.execute_step(
        workflow_run_id,
        user_id=user_id,
    )
    dispatch_after_step(user_id=user_id, result=result)
    return result


async def run_resume_workflow(
    *,
    user_id: str,
    workflow_run_id: str,
    service: WorkflowExecutionService | None = None,
) -> StepExecutionResult:
    execution = service or workflow_execution_service
    result = await execution.execute_step(
        workflow_run_id,
        user_id=user_id,
    )
    dispatch_after_step(user_id=user_id, result=result)
    return result
