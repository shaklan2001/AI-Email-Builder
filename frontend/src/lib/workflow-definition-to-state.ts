import { formatWaitLabel, waitLabelForStep } from "./format-wait-label";
import {
  defaultWorkflowState,
  type WorkflowState,
} from "../types/workflow-state";
import type { WorkflowDefinition, WorkflowStep } from "../types/workflow-definition";

function formatConditionLabel(condition: string): string {
  if (condition === "reply_received") {
    return "Reply?";
  }
  const words = condition.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1) + "?";
}

function stepLabel(step: WorkflowStep, definition: WorkflowDefinition | null): string {
  if (step.type === "send_email") {
    return step.name ?? "Send Email";
  }
  if (step.type === "wait") {
    return waitLabelForStep(step, definition?.followUpDelay);
  }
  if (step.type === "reply_condition") {
    return "Reply?";
  }
  if (step.type === "interested_branch") {
    return step.name ?? "AI Reply Agent";
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
  const conditionStep = definition.steps.find(
    (s) =>
      s.type === "reply_condition" ||
      (s.type === "condition" && s.condition === "reply_received"),
  );

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
    .map((s) => stepLabel(s, definition));

  const waitLabel = definition.followUpDelay
    ? formatWaitLabel(definition.followUpDelay)
    : waitStep
      ? stepLabel(waitStep, definition)
      : defaultWorkflowState.waitLabel;

  return {
    initialEmailLabel: initialEmail ? stepLabel(initialEmail, definition) : "Send Initial Email",
    waitLabel,
    conditionLabel: conditionStep
      ? stepLabel(conditionStep, definition)
      : defaultWorkflowState.conditionLabel,
    yesBranchLabel: conditionStep?.condition === "reply_received"
      ? "AI Reply Agent"
      : yesBranch
        ? stepLabel(yesBranch, definition)
        : sendEmails[1]
          ? stepLabel(sendEmails[1], definition)
          : defaultWorkflowState.yesBranchLabel,
    noBranchLabel: noBranch
      ? stepLabel(noBranch, definition)
      : sendEmails[2]
        ? stepLabel(sendEmails[2], definition)
        : defaultWorkflowState.noBranchLabel,
    extraSteps,
  };
}
