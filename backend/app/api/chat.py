from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.core.workflow_ids import assert_valid_workflow_id
from app.schemas.chat import ChatMessageRequest, ChatResetRequest, ChatResponseData, ChatThreadData
from app.schemas.responses import SuccessResponse
from app.services.chat_service import chat_service
from app.services.chat_thread_service import chat_thread_service

router = APIRouter()
logger = get_logger(__name__)


def _invalid_thread_id(exc: ValueError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


@router.post(
    "/message",
    response_model=SuccessResponse[ChatResponseData],
    response_model_by_alias=True,
)
async def send_message(
    body: ChatMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ChatResponseData]:
    thread_id = body.resolved_thread_id()
    assert thread_id is not None
    try:
        assert_valid_workflow_id(thread_id)
    except ValueError as exc:
        raise _invalid_thread_id(exc) from exc

    logger.info(
        "chat_message_received",
        user_id=current_user.user_id,
        thread_id=thread_id,
    )
    result = await chat_service.process_message(
        user_id=current_user.user_id,
        thread_id=thread_id,
        message=body.message,
    )
    return SuccessResponse(
        data=ChatResponseData(
            message=result.message,
            stage=result.stage,
            campaign_brief=result.campaign_brief,  # type: ignore[arg-type]
            workflow_preview=result.workflow_preview,
            brief_status=result.brief_status,
            review_status=result.review_status,
            activation_allowed=result.activation_allowed,
        ),
    )


@router.get(
    "/thread/{thread_id}",
    response_model=SuccessResponse[ChatThreadData],
    response_model_by_alias=True,
)
async def get_thread(
    thread_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ChatThreadData]:
    try:
        assert_valid_workflow_id(thread_id)
    except ValueError as exc:
        raise _invalid_thread_id(exc) from exc

    result = await chat_thread_service.get_thread(
        user_id=current_user.user_id,
        thread_id=thread_id,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    return SuccessResponse(data=result.data)


@router.post(
    "/reset",
    response_model=SuccessResponse[ChatThreadData],
    response_model_by_alias=True,
)
async def reset_thread(
    body: ChatResetRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ChatThreadData]:
    thread_id = body.resolved_thread_id()
    assert thread_id is not None
    try:
        assert_valid_workflow_id(thread_id)
    except ValueError as exc:
        raise _invalid_thread_id(exc) from exc

    logger.info(
        "chat_thread_reset",
        user_id=current_user.user_id,
        thread_id=thread_id,
    )
    result = await chat_thread_service.reset_thread(
        user_id=current_user.user_id,
        thread_id=thread_id,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    return SuccessResponse(data=result.data)
