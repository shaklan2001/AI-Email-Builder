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
  waitLabel: "Wait",
  conditionLabel: "Reply?",
  yesBranchLabel: "AI Reply Agent",
  noBranchLabel: "Follow Up Email",
  extraSteps: [],
};
