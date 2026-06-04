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

export interface WorkflowReviewData {
  workflowSummary: WorkflowSummary;
  emailSummary: EmailSummary;
  recipientCount: number;
  scheduleSummary: ScheduleSummary;
}
