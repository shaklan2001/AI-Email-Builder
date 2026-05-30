from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class SuccessResponse(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: T


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorDetail
