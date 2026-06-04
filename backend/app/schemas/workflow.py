from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.email import GeneratedEmailContent
from app.schemas.follow_up_delay import FollowUpDelay, FollowUpDelayUnit


WorkflowType = Literal["linear", "conditional", "multi_level_conditional"]
GenerationStepType = Literal[
    "send_email",
    "wait",
    "reply_condition",
    "interested_branch",
    "no_reply_branch",
]
LegacyStepType = Literal["condition", "end"]
StepType = GenerationStepType | LegacyStepType


class WorkflowStep(BaseModel):
    id: str = Field(..., min_length=1)
    type: StepType
    name: str | None = None
    days: int | None = Field(default=None, ge=1)
    value: int | None = Field(default=None, ge=1)
    unit: FollowUpDelayUnit | None = None
    condition: str | None = None
    branch: Literal["yes", "no"] | None = None
    email: GeneratedEmailContent | None = None


class WorkflowDefinition(BaseModel):
    workflow_type: WorkflowType | None = None
    follow_up_delay: FollowUpDelay | None = None
    steps: list[WorkflowStep] = Field(default_factory=list)

    def to_api_dict(self) -> dict[str, object]:
        data = self.model_dump(exclude_none=True)
        if self.workflow_type is None:
            data.pop("workflow_type", None)
        return data
