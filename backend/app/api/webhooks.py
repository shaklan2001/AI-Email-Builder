from fastapi import APIRouter, Request

from app.core.logger import get_logger
from app.schemas.requests import WebhookProcessData
from app.schemas.responses import SuccessResponse
from app.services.webhook_processing_service import webhook_processing_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("/resend", response_model=SuccessResponse[WebhookProcessData])
async def resend_webhook(request: Request) -> SuccessResponse[WebhookProcessData]:
    payload = await request.body()
    headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }
    logger.info("webhook_received", path="/api/v1/webhooks/resend")
    result = await webhook_processing_service.process(payload=payload, headers=headers)
    return SuccessResponse(
        data=WebhookProcessData(
            status=result.status,
            event_type=result.event_type,
            duplicate=result.duplicate,
            workflow_updated=result.workflow_updated,
        ),
    )
