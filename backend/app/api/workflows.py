from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.repositories.workflow_repository import WorkflowRecord, workflow_repository
from app.schemas.requests import (
    ActivateWorkflowData,
    AddRecipientsRequest,
    CreateWorkflowRequest,
    DeleteWorkflowData,
    RecipientItemData,
    RecipientListData,
    RecipientUploadData,
    RequeueWorkflowRunsData,
    UpdateWorkflowEmailRequest,
    UpdateWorkflowStatusData,
    UpdateWorkflowStatusRequest,
    WorkflowData,
    WorkflowDefinitionData,
    WorkflowSessionData,
)
from app.schemas.responses import SuccessResponse
from app.services.recipient_service import recipient_service
from app.services.workflow_activation_service import workflow_activation_service
from app.services.workflow_delete_service import workflow_delete_service
from app.services.workflow_email_service import workflow_email_service
from app.core.workflow_ids import assert_valid_workflow_id
from app.services.conversation_threads_service import (
    ConversationThreadSummaryData,
    conversation_threads_service,
)
from app.services.workflow_run_queue_service import workflow_run_queue_service
from app.services.workflow_session_service import workflow_session_service
from app.services.workflow_status_service import workflow_status_service

router = APIRouter()
logger = get_logger(__name__)


def _to_workflow_data(record: WorkflowRecord) -> WorkflowData:
    return WorkflowData(
        id=record.id,
        name=record.name,
        status=record.status,
        active_version=record.active_version,
        activated_at=record.activated_at.isoformat() if record.activated_at else None,
        created_at=record.created_at.isoformat(),
    )


def _to_recipient_items(raw: object) -> list[RecipientItemData]:
    if not isinstance(raw, list):
        return []
    items: list[RecipientItemData] = []
    for entry in raw:
        if isinstance(entry, dict):
            email = entry.get("email")
            if isinstance(email, str) and email.strip():
                items.append(RecipientItemData(email=email.strip()))
    return items


def _to_recipient_list_data(raw: dict[str, object]) -> RecipientListData:
    recipients = _to_recipient_items(raw.get("recipients"))
    valid_count = raw.get("valid_count")
    invalid_count = raw.get("invalid_count")
    return RecipientListData(
        recipients=recipients,
        valid_count=int(valid_count) if isinstance(valid_count, int) else len(recipients),
        invalid_count=int(invalid_count) if isinstance(invalid_count, int) else 0,
    )


def _to_recipient_upload_data(raw: dict[str, object]) -> RecipientUploadData:
    recipients = _to_recipient_items(raw.get("recipients"))
    valid_emails_raw = raw.get("valid_emails")
    valid_emails = (
        [email for email in valid_emails_raw if isinstance(email, str)]
        if isinstance(valid_emails_raw, list)
        else []
    )
    invalid_rows_raw = raw.get("invalid_rows")
    invalid_rows = (
        [row for row in invalid_rows_raw if isinstance(row, dict)]
        if isinstance(invalid_rows_raw, list)
        else []
    )
    valid_count = raw.get("valid_count")
    invalid_count = raw.get("invalid_count")
    return RecipientUploadData(
        recipients=recipients,
        valid_emails=valid_emails,
        invalid_rows=invalid_rows,
        valid_count=int(valid_count) if isinstance(valid_count, int) else len(recipients),
        invalid_count=int(invalid_count) if isinstance(invalid_count, int) else 0,
    )


def _validate_workflow_id(workflow_id: str) -> None:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=SuccessResponse[list[WorkflowData]])
async def list_workflows(
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[list[WorkflowData]]:
    records = await workflow_repository.list_by_user_id(current_user.user_id)
    logger.info(
        "workflows_listed",
        user_id=current_user.user_id,
        count=len(records),
    )
    return SuccessResponse(data=[_to_workflow_data(record) for record in records])


@router.post("", response_model=SuccessResponse[WorkflowData])
async def create_workflow(
    body: CreateWorkflowRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[WorkflowData]:
    workflow_id = f"wf_{uuid4().hex[:12]}"
    name = body.name or "Untitled Campaign"
    record = await workflow_repository.create(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        name=name,
        status="draft",
    )
    try:
        await workflow_session_service.initialize_empty_session(
            user_id=current_user.user_id,
            workflow_id=workflow_id,
        )
    except Exception:
        await workflow_repository.delete(
            user_id=current_user.user_id,
            workflow_id=workflow_id,
        )
        raise
    logger.info(
        "workflow_created",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        conversation_id=body.conversation_id,
    )
    return SuccessResponse(data=_to_workflow_data(record))


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


@router.get(
    "/{workflow_id}/recipients",
    response_model=SuccessResponse[RecipientListData],
    response_model_by_alias=True,
)
async def list_workflow_recipients(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[RecipientListData]:
    _validate_workflow_id(workflow_id)
    result = await recipient_service.list_recipients(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    logger.info(
        "workflow_recipients_listed",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        count=result.get("valid_count", 0),
    )
    return SuccessResponse(data=_to_recipient_list_data(result))


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
    _validate_workflow_id(workflow_id)
    result = await recipient_service.add_recipients(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        emails=body.emails,
    )
    logger.info(
        "workflow_recipients_added",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        valid_count=result.get("valid_count", 0),
        invalid_count=result.get("invalid_count", 0),
    )
    return SuccessResponse(data=_to_recipient_upload_data(result))


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
    _validate_workflow_id(workflow_id)
    updated, runs_enqueued = await workflow_status_service.update_status(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        new_status=body.status,
    )
    logger.info(
        "workflow_status_updated",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        status=updated.status,
        runs_enqueued=runs_enqueued,
    )
    return SuccessResponse(
        data=UpdateWorkflowStatusData(
            id=updated.id,
            name=updated.name,
            status=updated.status,
            active_version=updated.active_version,
            activated_at=updated.activated_at.isoformat() if updated.activated_at else None,
            created_at=updated.created_at.isoformat(),
            runs_enqueued=runs_enqueued,
        ),
    )


@router.post(
    "/{workflow_id}/runs/requeue",
    response_model=SuccessResponse[RequeueWorkflowRunsData],
    response_model_by_alias=True,
)
async def requeue_workflow_runs(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[RequeueWorkflowRunsData]:
    _validate_workflow_id(workflow_id)
    runs_enqueued = await workflow_run_queue_service.requeue_workflow_runs(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        require_active=True,
    )
    message = (
        f"Queued {runs_enqueued} email run(s). Check your inbox shortly."
        if runs_enqueued > 0
        else "No pending email runs to queue."
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


@router.post(
    "/{workflow_id}/activate",
    response_model=SuccessResponse[ActivateWorkflowData],
    response_model_by_alias=True,
)
async def activate_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ActivateWorkflowData]:
    _validate_workflow_id(workflow_id)
    result = await workflow_activation_service.activate(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    logger.info(
        "workflow_activated",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        active_version=result.active_version,
        runs_queued=result.runs_queued,
    )
    return SuccessResponse(data=result)


@router.delete(
    "/{workflow_id}",
    response_model=SuccessResponse[DeleteWorkflowData],
    response_model_by_alias=True,
)
async def delete_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[DeleteWorkflowData]:
    _validate_workflow_id(workflow_id)
    await workflow_delete_service.delete_workflow(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    logger.info(
        "workflow_deleted",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    return SuccessResponse(
        data=DeleteWorkflowData(
            workflow_id=workflow_id,
            message="Workflow deleted successfully.",
        ),
    )


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
    return SuccessResponse(data=_to_workflow_data(record))


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


@router.get(
    "/{workflow_id}/conversation-threads",
    response_model=SuccessResponse[list[ConversationThreadSummaryData]],
    response_model_by_alias=True,
)
async def list_conversation_threads(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[list[ConversationThreadSummaryData]]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    threads = await conversation_threads_service.list_for_workflow(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    return SuccessResponse(data=threads)


@router.get(
    "/{workflow_id}/conversation-threads/preview",
    response_model=SuccessResponse[ConversationThreadSummaryData | None],
    response_model_by_alias=True,
)
async def get_conversation_thread_preview(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ConversationThreadSummaryData | None]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    preview = await conversation_threads_service.preview_thread(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    return SuccessResponse(data=preview)
