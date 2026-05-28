from typing import Literal

from pydantic import BaseModel, Field

FollowUpDelayUnit = Literal["hours", "days", "weeks"]


class FollowUpDelay(BaseModel):
    value: int = Field(..., ge=1)
    unit: FollowUpDelayUnit

    def to_api_dict(self) -> dict[str, object]:
        return {"value": self.value, "unit": self.unit}
