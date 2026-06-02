from fastapi import APIRouter, Depends

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.schemas.requests import EmailSendStatusData, SendEmailRequest
from app.schemas.responses import SuccessResponse
from app.services.email_service import email_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("/send", response_model=SuccessResponse[EmailSendStatusData])
async def send_email(
    body: SendEmailRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[EmailSendStatusData]:
    logger.info(
        "email_send_requested",
        user_id=current_user.user_id,
        workflow_id=body.workflow_id,
    )
    result = await email_service.send_workflow_email(
        user_id=current_user.user_id,
        workflow_id=body.workflow_id,
    )
    logger.info(
        "email_send_completed",
        user_id=current_user.user_id,
        workflow_id=body.workflow_id,
        status=result.status,
        message_id=result.message_id,
    )
    return SuccessResponse(data=result)
