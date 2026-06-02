from fastapi import APIRouter, Depends

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.schemas.requests import ReviewData, ReviewRequest
from app.schemas.responses import SuccessResponse

router = APIRouter()
logger = get_logger(__name__)

MOCK_REVIEW_DATA = ReviewData(
    workflow_summary={
        "name": "Product Launch Follow-up",
        "description": "Multi-step email sequence for new signups with reply-based branching.",
        "steps": [
            "Send Initial Email",
            "Wait 3 Days",
            "Reply?",
            "Yes → Demo Call",
            "No → Follow Up Email",
        ],
    },
    email_summary={
        "subject": "Welcome — here's what you can do next",
        "body_preview": (
            "Hi there, thanks for signing up. We built this workflow to help you "
            "get started quickly. Reply to this email if you'd like a personalized demo."
        ),
    },
    recipient_count=128,
    schedule_summary={
        "start_date": "June 10, 2026",
        "timezone": "America/New_York (EST)",
        "send_window": "Weekdays, 9:00 AM – 5:00 PM",
    },
)


@router.post("", response_model=SuccessResponse[ReviewData])
async def submit_review(
    body: ReviewRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[ReviewData]:
    logger.info(
        "review_submitted",
        user_id=current_user.user_id,
        workflow_id=body.workflow_id,
    )
    return SuccessResponse(data=MOCK_REVIEW_DATA)
