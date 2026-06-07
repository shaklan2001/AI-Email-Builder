export type WorkflowType =
  | "linear"
  | "conditional"
  | "multi_level_conditional";

import type { FollowUpDelay } from "./follow-up-delay";

export type WorkflowStepType =
  | "send_email"
  | "wait"
  | "reply_condition"
  | "interested_branch"
  | "no_reply_branch"
  | "condition"
  | "end";

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
  value?: number;
  unit?: "minutes" | "hours" | "days" | "weeks";
  condition?: string;
  branch?: "yes" | "no";
  email?: GeneratedEmail;
}

export interface WorkflowDefinition {
  workflowType?: WorkflowType;
  followUpDelay?: FollowUpDelay;
  steps: WorkflowStep[];
}
