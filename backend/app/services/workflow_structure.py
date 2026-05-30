"""Canonical outreach workflow structure for the workflow generation agent."""

from __future__ import annotations

from app.schemas.follow_up_delay import FollowUpDelay
from app.schemas.workflow import WorkflowDefinition, WorkflowStep

GENERATION_STEP_TYPES = frozenset(
    {
        "send_email",
        "wait",
        "reply_condition",
        "interested_branch",
        "no_reply_branch",
    }
)


def _names_from_steps(steps: list[WorkflowStep]) -> tuple[str, str]:
    send_steps = [s for s in steps if s.type == "send_email"]
    initial = send_steps[0].name if send_steps and send_steps[0].name else "Initial Outreach"
    follow_up = (
        send_steps[-1].name
        if len(send_steps) > 1 and send_steps[-1].name
        else "Follow Up"
    )
    return initial, follow_up


def build_no_follow_up_workflow(
    *,
    initial_name: str = "Initial Outreach",
) -> WorkflowDefinition:
    """Initial email with reply handling only — no wait or follow-up."""
    return WorkflowDefinition(
        follow_up_delay=None,
        steps=[
            WorkflowStep(id="step_1", type="send_email", name=initial_name),
            WorkflowStep(id="step_2", type="reply_condition"),
            WorkflowStep(
                id="step_3",
                type="interested_branch",
                name="AI Reply Agent",
            ),
        ],
    )


def build_canonical_workflow(
    delay: FollowUpDelay,
    *,
    initial_name: str = "Initial Outreach",
    follow_up_name: str = "Follow Up",
) -> WorkflowDefinition:
    """Standard conditional outreach: initial email → wait → reply branch."""
    return WorkflowDefinition(
        follow_up_delay=delay,
        steps=[
            WorkflowStep(id="step_1", type="send_email", name=initial_name),
            WorkflowStep(
                id="step_2",
                type="wait",
                value=delay.value,
                unit=delay.unit,
                days=wait_days_for_step(delay),
            ),
            WorkflowStep(id="step_3", type="reply_condition"),
            WorkflowStep(
                id="step_4",
                type="interested_branch",
                name="AI Reply Agent",
            ),
            WorkflowStep(id="step_5", type="no_reply_branch"),
            WorkflowStep(id="step_6", type="send_email", name=follow_up_name),
        ],
    )


def wait_days_for_step(delay: FollowUpDelay) -> int:
    if delay.unit == "days":
        return delay.value
    if delay.unit == "weeks":
        return delay.value * 7
    return max(1, (delay.value + 23) // 24)


def is_valid_generation_workflow(steps: list[WorkflowStep]) -> bool:
    if len(steps) < 5:
        return False
    types = [s.type for s in steps]
    if types[0] != "send_email" or "wait" not in types:
        return False
    if "reply_condition" not in types:
        return False
    if "interested_branch" not in types or "no_reply_branch" not in types:
        return False
    send_count = sum(1 for s in steps if s.type == "send_email")
    return send_count >= 2


def apply_delay_to_workflow(
    definition: WorkflowDefinition,
    delay: FollowUpDelay,
) -> WorkflowDefinition:
    updated_steps: list[WorkflowStep] = []
    for step in definition.steps:
        if step.type == "wait":
            updated_steps.append(
                step.model_copy(
                    update={
                        "value": delay.value,
                        "unit": delay.unit,
                        "days": wait_days_for_step(delay),
                    },
                ),
            )
        else:
            updated_steps.append(step)
    return definition.model_copy(
        update={"follow_up_delay": delay, "steps": updated_steps},
    )


def finalize_generation_workflow(
    definition: WorkflowDefinition,
    delay: FollowUpDelay | None,
    *,
    wants_follow_up: bool = True,
) -> WorkflowDefinition:
    """Validate LLM output; repair structure and timing from user preferences."""
    steps = list(definition.steps)
    initial_name, follow_up_name = _names_from_steps(steps)

    if not wants_follow_up:
        return build_no_follow_up_workflow(initial_name=initial_name)

    if delay is None:
        delay = FollowUpDelay(value=3, unit="days")

    if not is_valid_generation_workflow(steps):
        definition = build_canonical_workflow(
            delay,
            initial_name=initial_name,
            follow_up_name=follow_up_name,
        )
    else:
        definition = apply_delay_to_workflow(definition, delay)
    return definition


def uses_generation_step_types(steps: list[WorkflowStep]) -> bool:
    return any(s.type in GENERATION_STEP_TYPES for s in steps)


def normalize_for_execution(definition: WorkflowDefinition) -> WorkflowDefinition:
    """Map generation node types to execution engine types (condition / branch / end)."""
    if not uses_generation_step_types(definition.steps):
        return definition

    legacy_steps: list[WorkflowStep] = []
    past_reply_condition = False

    for step in definition.steps:
        if step.type == "reply_condition":
            past_reply_condition = True
            legacy_steps.append(
                WorkflowStep(
                    id=step.id,
                    type="condition",
                    condition="reply_received",
                ),
            )
            continue
        if step.type == "interested_branch":
            legacy_steps.append(
                WorkflowStep(
                    id=step.id,
                    type="end",
                    name=step.name,
                    branch="yes",
                ),
            )
            continue
        if step.type == "no_reply_branch":
            continue
        if step.type == "send_email" and past_reply_condition:
            legacy_steps.append(step.model_copy(update={"branch": "no"}))
            continue
        legacy_steps.append(step)

    workflow_type = definition.workflow_type or "conditional"
    return definition.model_copy(
        update={"workflow_type": workflow_type, "steps": legacy_steps},
    )
