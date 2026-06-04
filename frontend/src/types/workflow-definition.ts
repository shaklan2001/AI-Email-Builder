export type WorkflowType =
  | "linear"
  | "conditional"
  | "multi_level_conditional";

export type WorkflowStepType = "send_email" | "wait" | "condition" | "end";

export interface EmailBodyVersion {
  subject: string;
  htmlContent: string;
  plainTextContent: string;
}

export interface GeneratedEmail {
  aiGeneratedVersion: EmailBodyVersion;
  finalUserVersion: EmailBodyVersion;
  userEdited: boolean;
}

export interface WorkflowStep {
  id: string;
  type: WorkflowStepType;
  name?: string;
  days?: number;
  condition?: string;
  branch?: "yes" | "no";
  email?: GeneratedEmail;
}

export interface WorkflowDefinition {
  workflowType?: WorkflowType;
  steps: WorkflowStep[];
}
