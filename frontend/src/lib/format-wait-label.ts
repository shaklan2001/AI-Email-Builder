import type { FollowUpDelay } from "../types/follow-up-delay";
import type { WorkflowDefinition, WorkflowStep } from "../types/workflow-definition";

export function formatWaitLabel(delay: FollowUpDelay): string {
  if (delay.unit === "hours") {
    const label = delay.value === 1 ? "Hour" : "Hours";
    return `Wait ${delay.value} ${label}`;
  }
  if (delay.unit === "weeks") {
    const label = delay.value === 1 ? "Week" : "Weeks";
    return `Wait ${delay.value} ${label}`;
  }
  const label = delay.value === 1 ? "Day" : "Days";
  return `Wait ${delay.value} ${label}`;
}

export function waitLabelForStep(
  step: WorkflowStep,
  followUpDelay?: FollowUpDelay | null,
): string {
  if (
    step.type === "wait" &&
    step.value != null &&
    (step.unit === "hours" || step.unit === "days" || step.unit === "weeks")
  ) {
    return formatWaitLabel({ value: step.value, unit: step.unit });
  }
  if (step.type === "wait" && followUpDelay) {
    return formatWaitLabel(followUpDelay);
  }
  if (step.type === "wait" && step.days != null) {
    const dayWord = step.days === 1 ? "Day" : "Days";
    return `Wait ${step.days} ${dayWord}`;
  }
  if (step.type === "wait") {
    return "Wait";
  }
  return step.name ?? step.type;
}

export function waitLabelFromDefinition(definition: WorkflowDefinition | null): string | null {
  if (!definition?.followUpDelay) {
    return null;
  }
  return formatWaitLabel(definition.followUpDelay);
}
