from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.repositories.workflow_repository import workflow_repository
from app.schemas.requests import (
    CreateWorkflowRequest,
    UpdateWorkflowEmailRequest,
    WorkflowData,
    WorkflowDefinitionData,
    WorkflowSessionData,
)
from app.schemas.responses import SuccessResponse
from app.services.workflow_email_service import workflow_email_service
from app.core.workflow_ids import assert_valid_workflow_id
from app.services.workflow_session_service import workflow_session_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("", response_model=SuccessResponse[WorkflowData])
async def create_workflow(
    body: CreateWorkflowRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[WorkflowData]:
    workflow_id = f"wf_{uuid4().hex[:12]}"
    name = body.name or "Untitled Workflow"
    record = await workflow_repository.create(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        name=name,
        status="draft",
    )
    await workflow_session_service.initialize_empty_session(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    logger.info(
        "workflow_created",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        conversation_id=body.conversation_id,
    )
    return SuccessResponse(
        data=WorkflowData(
            id=record.id,
            name=record.name,
            status=record.status,
            created_at=record.created_at.isoformat(),
        )
    )


@router.get(
    "/{workflow_id}/session",
    response_model=SuccessResponse[WorkflowSessionData],
    response_model_by_alias=True,
)
async def get_workflow_session(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[WorkflowSessionData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    result = await workflow_session_service.get_session(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return SuccessResponse(data=result.session)


@router.get("/{workflow_id}", response_model=SuccessResponse[WorkflowData])
async def get_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[WorkflowData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    record = await workflow_repository.get_by_id(current_user.user_id, workflow_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    logger.info(
        "workflow_fetched",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    return SuccessResponse(
        data=WorkflowData(
            id=record.id,
            name=record.name,
            status=record.status,
            created_at=record.created_at.isoformat(),
        )
    )


@router.patch(
    "/{workflow_id}/emails/{step_id}",
    response_model=SuccessResponse[WorkflowDefinitionData],
    response_model_by_alias=True,
)
async def update_workflow_email(
    workflow_id: str,
    step_id: str,
    body: UpdateWorkflowEmailRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[WorkflowDefinitionData]:
    logger.info(
        "workflow_email_updated",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        step_id=step_id,
    )
    workflow = await workflow_email_service.update_step_email(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        step_id=step_id,
        body=body,
    )
    return SuccessResponse(data=workflow)
