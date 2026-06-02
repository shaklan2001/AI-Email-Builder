import json
import re

from langsmith import traceable

from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.schemas.campaign import CampaignData
from app.schemas.follow_up_delay import FollowUpDelay
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.workflow_structure import (
    GENERATION_STEP_TYPES,
    finalize_generation_workflow,
)

_WORKFLOW_SYSTEM = """You are a sales email automation strategist designing outreach workflows.
Analyze the campaign information and produce a workflow definition as JSON only.

Output shape (ONLY this object, no markdown):
{
  "steps": [
    { "id": "step_1", "type": "send_email", "name": "short step purpose label" },
    { "id": "step_2", "type": "wait" },
    { "id": "step_3", "type": "reply_condition" },
    { "id": "step_4", "type": "interested_branch", "name": "AI Reply Agent" },
    { "id": "step_5", "type": "no_reply_branch" },
    { "id": "step_6", "type": "send_email", "name": "follow-up step purpose label" }
  ]
}

Allowed step types ONLY: send_email, wait, reply_condition, interested_branch, no_reply_branch

Rules:
- Do NOT include email body, subject lines, or HTML — structure only.
- Always include exactly this flow order: initial send_email → wait → reply_condition → interested_branch → no_reply_branch → follow-up send_email.
- send_email steps need a short descriptive "name" (purpose, not email copy).
- wait step has no timing fields — follow-up delay is applied from user settings after generation.
- reply_condition, interested_branch, and no_reply_branch are single nodes with no extra fields except optional "name" on interested_branch.
- Use unique step ids: step_1, step_2, etc.
- Return ONLY valid JSON."""


def _parse_json_object(text: str) -> dict[str, object]:
    cleaned = text.strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
    if fence:
        try:
            parsed = json.loads(fence.group(1).strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    brace = re.search(r"\{[\s\S]*\}", cleaned)
    if brace:
        try:
            parsed = json.loads(brace.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {}


def _validate_workflow_payload(raw: dict[str, object]) -> WorkflowDefinition:
    steps_raw = raw.get("steps")
    if not isinstance(steps_raw, list):
        return WorkflowDefinition(steps=[])

    steps: list[WorkflowStep] = []
    for item in steps_raw:
        if not isinstance(item, dict):
            continue
        step_type = item.get("type")
        if step_type not in GENERATION_STEP_TYPES:
            continue
        step_id = item.get("id")
        if not isinstance(step_id, str) or not step_id.strip():
            continue
        try:
            steps.append(WorkflowStep.model_validate(item))
        except Exception:
            continue

    return WorkflowDefinition(steps=steps)


class WorkflowAgent:
    """Analyzes campaign state and generates a structured workflow definition."""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        return get_groq_provider()

    @traceable(run_type="chain", name="workflow_generation")
    async def generate_workflow(
        self,
        campaign: CampaignData,
        *,
        follow_up_delay: FollowUpDelay | None,
        wants_follow_up: bool = True,
    ) -> tuple[WorkflowDefinition, str]:
        if wants_follow_up and follow_up_delay is not None:
            delay_note = f"{follow_up_delay.value} {follow_up_delay.unit}"
            follow_up_line = f"Follow-up if no reply: {delay_note}\n\n"
        else:
            follow_up_line = (
                "Follow-up if no reply: disabled — user chose initial email only.\n\n"
            )

        user_prompt = (
            f"{campaign.authoritative_summary()}\n\n"
            f"{follow_up_line}"
            "Design the workflow structure for this campaign. "
            "Use ONLY the campaign brief above. "
            "Name the initial and follow-up send_email steps to match the campaign goal."
        )

        llm = self._get_llm()
        try:
            raw_text = await llm.generate(_WORKFLOW_SYSTEM, user_prompt)
        except LLMProviderError as exc:
            raise exc

        parsed = _validate_workflow_payload(_parse_json_object(raw_text))
        definition = finalize_generation_workflow(
            parsed,
            follow_up_delay,
            wants_follow_up=wants_follow_up,
        )
        if not definition.steps:
            raise LLMProviderError("Workflow generation returned no valid steps")

        reply = self._build_acknowledgement(
            definition,
            follow_up_delay,
            wants_follow_up=wants_follow_up,
        )
        return definition, reply

    @staticmethod
    def _build_acknowledgement(
        definition: WorkflowDefinition,
        delay: FollowUpDelay | None,
        *,
        wants_follow_up: bool = True,
    ) -> str:
        from app.services.follow_up_delay import format_wait_label

        step_count = len(definition.steps)
        if wants_follow_up and delay is not None:
            wait_label = format_wait_label(delay)
            return (
                f"I've built your outreach workflow with {step_count} steps — "
                f"initial email, {wait_label.lower()}, then a reply branch with AI handling "
                "interested replies and a follow-up if there's no reply. "
                "Review the preview on the right and tell me if you'd like to adjust timing or step names."
            )
        return (
            f"I've built your outreach workflow with {step_count} steps — "
            "initial email and AI reply handling when someone responds. "
            "No follow-up email will be sent if there's no reply. "
            "Review the preview on the right and tell me if you'd like any changes."
        )


workflow_agent = WorkflowAgent()
