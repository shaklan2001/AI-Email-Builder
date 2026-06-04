from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.repositories.workflow_repository import WorkflowRecord, workflow_repository
from app.schemas.requests import (
    ActivateWorkflowData,
    AddRecipientsRequest,
    CreateWorkflowRequest,
    RecipientListData,
    RecipientUploadData,
    UpdateWorkflowEmailRequest,
    RequeueWorkflowRunsData,
    UpdateWorkflowStatusData,
    UpdateWorkflowStatusRequest,
    WorkflowData,
    WorkflowDefinitionData,
    WorkflowSessionData,
)
from app.services.recipient_service import recipient_service
from app.schemas.responses import SuccessResponse
from app.services.workflow_activation_service import workflow_activation_service
from app.services.workflow_run_queue_service import workflow_run_queue_service
from app.services.workflow_status_service import workflow_status_service
from app.services.workflow_email_service import workflow_email_service
from app.core.workflow_ids import assert_valid_workflow_id
from app.services.workflow_session_service import workflow_session_service

router = APIRouter()
logger = get_logger(__name__)


def _workflow_data(record: WorkflowRecord) -> WorkflowData:
    return WorkflowData(
        id=record.id,
        name=record.name,
        status=record.status,
        active_version=record.active_version,
        activated_at=record.activated_at.isoformat() if record.activated_at else None,
        created_at=record.created_at.isoformat(),
    )


@router.get("", response_model=SuccessResponse[list[WorkflowData]])
async def list_workflows(
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[list[WorkflowData]]:
    records = await workflow_repository.list_for_user(current_user.user_id)
    logger.info(
        "workflows_listed",
        user_id=current_user.user_id,
        count=len(records),
    )
    return SuccessResponse(data=[_workflow_data(record) for record in records])


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
    return SuccessResponse(data=_workflow_data(record))


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
    return SuccessResponse(data=_workflow_data(record))


@router.get(
    "/{workflow_id}/recipients",
    response_model=SuccessResponse[RecipientListData],
    response_model_by_alias=True,
)
async def list_workflow_recipients(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[RecipientListData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    data = await recipient_service.list_recipients(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    return SuccessResponse(data=RecipientListData.model_validate(data))


@router.post(
    "/{workflow_id}/recipients",
    response_model=SuccessResponse[RecipientUploadData],
    response_model_by_alias=True,
)
async def add_workflow_recipients(
    workflow_id: str,
    body: AddRecipientsRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[RecipientUploadData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    data = await recipient_service.add_recipients(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        emails=body.emails,
    )
    logger.info(
        "workflow_recipients_added",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        valid_count=data["valid_count"],
    )
    return SuccessResponse(data=RecipientUploadData.model_validate(data))


@router.post(
    "/{workflow_id}/activate",
    response_model=SuccessResponse[ActivateWorkflowData],
    response_model_by_alias=True,
)
async def activate_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ActivateWorkflowData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    result = await workflow_activation_service.activate(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    logger.info(
        "workflow_activated",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        runs_queued=result.runs_queued,
    )
    return SuccessResponse(data=result)


def _workflow_status_data(record: WorkflowRecord, *, runs_enqueued: int = 0) -> UpdateWorkflowStatusData:
    base = _workflow_data(record)
    return UpdateWorkflowStatusData(
        id=base.id,
        name=base.name,
        status=base.status,
        active_version=base.active_version,
        activated_at=base.activated_at,
        created_at=base.created_at,
        runs_enqueued=runs_enqueued,
    )


@router.patch(
    "/{workflow_id}/status",
    response_model=SuccessResponse[UpdateWorkflowStatusData],
    response_model_by_alias=True,
)
async def update_workflow_status(
    workflow_id: str,
    body: UpdateWorkflowStatusRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[UpdateWorkflowStatusData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    record, runs_enqueued = await workflow_status_service.update_status(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        new_status=body.status,
    )
    logger.info(
        "workflow_status_updated",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        status=record.status,
        runs_enqueued=runs_enqueued,
    )
    return SuccessResponse(data=_workflow_status_data(record, runs_enqueued=runs_enqueued))


@router.post(
    "/{workflow_id}/runs/requeue",
    response_model=SuccessResponse[RequeueWorkflowRunsData],
    response_model_by_alias=True,
)
async def requeue_workflow_runs(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[RequeueWorkflowRunsData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    runs_enqueued = await workflow_run_queue_service.requeue_workflow_runs(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    message = (
        f"Queued {runs_enqueued} run(s) for processing."
        if runs_enqueued
        else "No pending runs to queue."
    )
    logger.info(
        "workflow_runs_requeued",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        runs_enqueued=runs_enqueued,
    )
    return SuccessResponse(
        data=RequeueWorkflowRunsData(
            workflow_id=workflow_id,
            runs_enqueued=runs_enqueued,
            message=message,
        ),
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
