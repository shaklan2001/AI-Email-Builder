import type { LeadDetails } from "./lead-details";
import type { LeadStatus } from "./lead-status";

export type LeadStatusCounts = Record<LeadStatus, number>;

export interface WorkflowSummary {
  name: string;
  description: string;
  steps: string[];
}

export interface EmailSummary {
  subject: string;
  bodyPreview: string;
}

export interface ScheduleSummary {
  startDate: string;
  timezone: string;
  sendWindow: string;
}

export type ReviewStatus = "pending" | "approved" | "editing" | null;

export interface WorkflowReviewData {
  workflowSummary: WorkflowSummary;
  emailSummary: EmailSummary;
  recipientCount: number;
  scheduleSummary: ScheduleSummary;
  reviewStatus?: ReviewStatus;
  activationAllowed?: boolean;
  leadStatusCounts?: LeadStatusCounts;
  leadDetails?: LeadDetails[];
}
