import { normalizeGeneratedEmail } from "./email-content";
import type { FollowUpDelay } from "../types/follow-up-delay";
import type { WorkflowDefinition } from "../types/workflow-definition";

type RawWorkflowDefinition = WorkflowDefinition & {
  workflow_type?: WorkflowDefinition["workflowType"];
  follow_up_delay?: FollowUpDelay;
};

export function parseWorkflowDefinition(
  raw: RawWorkflowDefinition | null | undefined,
): WorkflowDefinition | null {
  if (!raw || !Array.isArray(raw.steps)) {
    return null;
  }

  const followUpDelay = raw.followUpDelay ?? raw.follow_up_delay;
  const parsedDelay =
    followUpDelay &&
    typeof followUpDelay.value === "number" &&
    (followUpDelay.unit === "hours" ||
      followUpDelay.unit === "days" ||
      followUpDelay.unit === "weeks")
      ? followUpDelay
      : undefined;

  return {
    workflowType: raw.workflowType ?? raw.workflow_type,
    followUpDelay: parsedDelay,
    steps: raw.steps.map((step) => {
      const email = step.email ? normalizeGeneratedEmail(step.email) : undefined;
      return {
        id: step.id,
        type: step.type,
        name: step.name,
        days: step.days,
        value: step.value,
        unit: step.unit,
        condition: step.condition,
        branch: step.branch,
        email,
      };
    }),
  };
}
