from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import CurrentUser, get_current_user
from app.core.workflow_ids import assert_valid_workflow_id
from app.repositories.workflow_repository import workflow_repository
from app.schemas.agent_tools_api import AgentToolsRunData, RunAgentToolsRequest, ToolExecutionData
from app.schemas.responses import SuccessResponse
from app.services.agent_tools_service import agent_tools_service

router = APIRouter()


@router.post(
    "/{workflow_id}/agent-tools/run",
    response_model=SuccessResponse[AgentToolsRunData],
)
async def run_agent_tools(
    workflow_id: str,
    body: RunAgentToolsRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[AgentToolsRunData]:
    assert_valid_workflow_id(workflow_id)
    record = await workflow_repository.get_by_id(current_user.user_id, workflow_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    result = await agent_tools_service.run_for_prospect_message(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        lead_email=body.lead_email,
        prospect_message=body.message,
    )

    return SuccessResponse(
        data=AgentToolsRunData(
            selectedTool=result.selected_tool.value,
            toolCalled=result.tool_called,
            toolResult=result.tool_result,
            agentResponse=result.agent_response,
            executionId=result.execution_id,
        ),
    )


@router.get(
    "/{workflow_id}/agent-tools/history",
    response_model=SuccessResponse[list[ToolExecutionData]],
)
async def list_tool_executions(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[list[ToolExecutionData]]:
    assert_valid_workflow_id(workflow_id)
    record = await workflow_repository.get_by_id(current_user.user_id, workflow_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    rows = await agent_tools_service.list_executions(workflow_id)
    return SuccessResponse(
        data=[
            ToolExecutionData(
                id=row.id,
                toolName=row.tool_name,
                leadEmail=row.lead_email,
                prospectMessage=row.prospect_message,
                agentResponse=row.agent_response,
                createdAt=row.created_at.isoformat(),
            )
            for row in rows
        ],
    )
