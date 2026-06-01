from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.core.workflow_ids import assert_valid_workflow_id
from app.schemas.requests import ReviewData
from app.schemas.responses import SuccessResponse
from app.services.review_service import review_service

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/{workflow_id}",
    response_model=SuccessResponse[ReviewData],
    response_model_by_alias=True,
)
async def get_workflow_review(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ReviewData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    data = await review_service.get_review(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    return SuccessResponse(data=data)


@router.post(
    "/{workflow_id}/approve",
    response_model=SuccessResponse[ReviewData],
    response_model_by_alias=True,
)
async def approve_workflow_review(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ReviewData]:
    try:
        assert_valid_workflow_id(workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    data = await review_service.approve(
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    logger.info(
        "workflow_review_approved",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
    )
    return SuccessResponse(data=data)
