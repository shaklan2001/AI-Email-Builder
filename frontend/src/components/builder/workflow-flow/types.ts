import type { GeneratedEmail } from "../../../types/workflow-definition";

export type WorkflowFlowNodeType =
  | "emailNode"
  | "waitNode"
  | "conditionNode"
  | "aiReplyAgentNode";

export interface EmailNodeData {
  label: string;
  email: GeneratedEmail;
  variant?: "default" | "branch";
  [key: string]: unknown;
}

export interface WaitNodeData {
  label: string;
  [key: string]: unknown;
}

export interface ConditionNodeData {
  label: string;
  [key: string]: unknown;
}

export interface AiReplyAgentNodeData {
  campaignId?: string;
  [key: string]: unknown;
}
