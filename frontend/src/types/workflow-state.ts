export interface WorkflowState {
  initialEmailLabel: string;
  waitLabel: string;
  conditionLabel: string;
  yesBranchLabel: string;
  noBranchLabel: string;
  extraSteps: string[];
}

export const defaultWorkflowState: WorkflowState = {
  initialEmailLabel: "Send Initial Email",
  waitLabel: "Wait 3 Days",
  conditionLabel: "Reply?",
  yesBranchLabel: "Demo Call",
  noBranchLabel: "Follow Up Email",
  extraSteps: [],
};
