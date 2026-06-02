from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.schemas.requests import ChatMessageData, ChatMessageRequest
from app.schemas.responses import SuccessResponse
from app.services.chat_service import chat_service
from app.core.workflow_ids import assert_valid_workflow_id

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/message",
    response_model=SuccessResponse[ChatMessageData],
    response_model_by_alias=True,
)
async def send_message(
    body: ChatMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ChatMessageData]:
    try:
        assert_valid_workflow_id(body.workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.info(
        "chat_message_received",
        user_id=current_user.user_id,
        workflow_id=body.workflow_id,
    )
    result = await chat_service.process_message(
        user_id=current_user.user_id,
        workflow_id=body.workflow_id,
        message=body.message,
    )
    return SuccessResponse(
        data=ChatMessageData(
            message=result.message,
            workflow=result.workflow,
            campaign_brief=result.campaign_brief,
            brief_status=result.brief_status,
        ),
    )
