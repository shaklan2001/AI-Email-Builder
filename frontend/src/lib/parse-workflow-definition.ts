import { normalizeGeneratedEmail } from "./email-content";
import type { WorkflowDefinition } from "../types/workflow-definition";

type RawWorkflowDefinition = WorkflowDefinition & {
  workflow_type?: WorkflowDefinition["workflowType"];
};

export function parseWorkflowDefinition(
  raw: RawWorkflowDefinition | null | undefined,
): WorkflowDefinition | null {
  if (!raw || !Array.isArray(raw.steps)) {
    return null;
  }

  return {
    workflowType: raw.workflowType ?? raw.workflow_type,
    steps: raw.steps.map((step) => {
      const email = step.email ? normalizeGeneratedEmail(step.email) : undefined;
      return {
        id: step.id,
        type: step.type,
        name: step.name,
        days: step.days,
        condition: step.condition,
        branch: step.branch,
        email,
      };
    }),
  };
}
