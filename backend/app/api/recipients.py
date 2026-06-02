from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.logger import get_logger
from app.core.security import CurrentUser, get_current_user
from app.schemas.requests import RecipientUploadData
from app.schemas.responses import SuccessResponse

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=SuccessResponse[RecipientUploadData])
async def upload_recipients(
    workflow_id: str = Form(..., min_length=1),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> SuccessResponse[RecipientUploadData]:
    logger.info(
        "recipients_uploaded",
        user_id=current_user.user_id,
        workflow_id=workflow_id,
        filename=file.filename,
    )
    return SuccessResponse(
        data=RecipientUploadData(
            valid_count=128,
            invalid_count=3,
            valid_emails=[
                "user1@example.com",
                "user2@example.com",
                "user3@example.com",
            ],
            invalid_rows=[
                {"row": 5, "email": "not-an-email", "reason": "Invalid email format"},
                {"row": 12, "email": "", "reason": "Email is required"},
                {"row": 47, "email": "bad@", "reason": "Invalid email format"},
            ],
        )
    )
