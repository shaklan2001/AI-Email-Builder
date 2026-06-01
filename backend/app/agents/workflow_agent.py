import json
import re

from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.schemas.campaign import CampaignData
from app.schemas.workflow import WorkflowDefinition, WorkflowStep, WorkflowType

_WORKFLOW_SYSTEM = """You are a sales and marketing campaign strategist designing email automation workflows.
Analyze the collected campaign information and produce a workflow definition as JSON only.

Supported workflow types (set workflow_type accordingly):
- linear: sequential steps only
- conditional: includes at least one condition branch (e.g. reply_received)
- multi_level_conditional: multiple nested or chained conditions

Step types allowed: send_email, wait, condition, end

Rules:
- Do NOT include email body content, subject lines, or sending actions — only workflow structure.
- send_email steps need a short descriptive "name" (step purpose, not email copy).
- wait steps need "days" (positive integer).
- condition steps need "condition" (e.g. reply_received, link_clicked).
- For conditional workflows, tag branch steps with "branch": "yes" or "branch": "no".
- Use unique step ids like step_1, step_2, etc.
- Return ONLY valid JSON with this shape:
{
  "workflow_type": "linear" | "conditional" | "multi_level_conditional",
  "steps": [
    { "id": "step_1", "type": "send_email", "name": "..." },
    { "id": "step_2", "type": "wait", "days": 3 },
    { "id": "step_3", "type": "condition", "condition": "reply_received" },
    { "id": "step_4", "type": "send_email", "name": "...", "branch": "no" }
  ]
}"""


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
        try:
            steps.append(WorkflowStep.model_validate(item))
        except Exception:
            continue

    workflow_type_raw = raw.get("workflow_type")
    workflow_type: WorkflowType | None = None
    if workflow_type_raw in ("linear", "conditional", "multi_level_conditional"):
        workflow_type = workflow_type_raw

    return WorkflowDefinition(workflow_type=workflow_type, steps=steps)


class WorkflowAgent:
    """Analyzes campaign state and generates a structured workflow definition."""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        return get_groq_provider()

    async def generate_workflow(
        self,
        campaign: CampaignData,
    ) -> tuple[WorkflowDefinition, str]:
        user_prompt = (
            f"{campaign.authoritative_summary()}\n\n"
            "Design the best workflow structure for this campaign. "
            "Use ONLY the campaign brief above — ignore any other products or goals. "
            "Choose linear, conditional, or multi_level_conditional based on the goals."
        )

        llm = self._get_llm()
        try:
            raw_text = await llm.generate(_WORKFLOW_SYSTEM, user_prompt)
        except LLMProviderError as exc:
            raise exc

        definition = _validate_workflow_payload(_parse_json_object(raw_text))
        if not definition.steps:
            raise LLMProviderError("Workflow generation returned no valid steps")

        reply = self._build_acknowledgement(definition)
        return definition, reply

    @staticmethod
    def _build_acknowledgement(definition: WorkflowDefinition) -> str:
        step_count = len(definition.steps)
        wf_type = definition.workflow_type or "custom"
        return (
            f"I've drafted a {wf_type.replace('_', ' ')} workflow with {step_count} steps "
            "based on your campaign details. Review the preview on the right — "
            "tell me if you'd like to adjust timing, branches, or add steps."
        )


workflow_agent = WorkflowAgent()
