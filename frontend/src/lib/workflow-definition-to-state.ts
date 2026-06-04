import {
  defaultWorkflowState,
  type WorkflowState,
} from "../types/workflow-state";
import type { WorkflowDefinition, WorkflowStep } from "../types/workflow-definition";

function formatConditionLabel(condition: string): string {
  const words = condition.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1) + "?";
}

function stepLabel(step: WorkflowStep): string {
  if (step.type === "send_email") {
    return step.name ?? "Send Email";
  }
  if (step.type === "wait") {
    const days = step.days ?? 3;
    const dayWord = days === 1 ? "Day" : "Days";
    return `Wait ${days} ${dayWord}`;
  }
  if (step.type === "condition" && step.condition) {
    return formatConditionLabel(step.condition);
  }
  if (step.type === "end") {
    return "End";
  }
  return step.name ?? step.type;
}

/** Maps API workflow JSON to legacy preview state for draft persistence. */
export function workflowDefinitionToState(
  definition: WorkflowDefinition | null,
): WorkflowState {
  if (!definition?.steps.length) {
    return defaultWorkflowState;
  }

  const sendEmails = definition.steps.filter((s) => s.type === "send_email");
  const waitStep = definition.steps.find((s) => s.type === "wait");
  const conditionStep = definition.steps.find((s) => s.type === "condition");

  const yesBranch = definition.steps.find(
    (s) => s.type === "send_email" && s.branch === "yes",
  );
  const noBranch = definition.steps.find(
    (s) => s.type === "send_email" && s.branch === "no",
  );

  const initialEmail = sendEmails[0];
  const extraSteps = sendEmails
    .slice(1)
    .filter((s) => s.branch !== "yes" && s.branch !== "no")
    .map(stepLabel);

  return {
    initialEmailLabel: initialEmail ? stepLabel(initialEmail) : "Send Initial Email",
    waitLabel: waitStep ? stepLabel(waitStep) : defaultWorkflowState.waitLabel,
    conditionLabel: conditionStep
      ? stepLabel(conditionStep)
      : defaultWorkflowState.conditionLabel,
    yesBranchLabel: yesBranch
      ? stepLabel(yesBranch)
      : sendEmails[1]
        ? stepLabel(sendEmails[1])
        : defaultWorkflowState.yesBranchLabel,
    noBranchLabel: noBranch
      ? stepLabel(noBranch)
      : sendEmails[2]
        ? stepLabel(sendEmails[2])
        : defaultWorkflowState.noBranchLabel,
    extraSteps,
  };
}
