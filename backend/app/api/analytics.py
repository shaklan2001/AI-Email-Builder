from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.core.workflow_ids import assert_valid_workflow_id
from app.schemas.requests import AnalyticsData
from app.schemas.responses import SuccessResponse
from app.services.analytics_service import analytics_service

router = APIRouter()
logger = get_logger(__name__)


@router.get("/{workflow_id}", response_model=SuccessResponse[AnalyticsData])
async def get_workflow_analytics(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[AnalyticsData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    metrics = await analytics_service.get_for_user(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    logger.info(
        "analytics_fetched",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    return SuccessResponse(
        data=AnalyticsData(
            sent=metrics.sent,
            delivered=metrics.delivered,
            opened=metrics.opened,
            clicked=metrics.clicked,
            replied=metrics.replied,
            failed=metrics.failed,
            bounced=metrics.bounced,
        )
    )
