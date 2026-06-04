import type { WorkflowReviewData } from "../types/workflow-review";

export const mockWorkflowReview: WorkflowReviewData = {
  workflowSummary: {
    name: "Product Launch Follow-up",
    description: "Multi-step email sequence for new signups with reply-based branching.",
    steps: [
      "Send Initial Email",
      "Wait 3 Days",
      "Reply?",
      "Yes → Demo Call",
      "No → Follow Up Email",
    ],
  },
  emailSummary: {
    subject: "Welcome — here's what you can do next",
    bodyPreview:
      "Hi there, thanks for signing up. We built this workflow to help you get started quickly. Reply to this email if you'd like a personalized demo, or we'll follow up in a few days with more tips.",
  },
  recipientCount: 128,
  scheduleSummary: {
    startDate: "June 10, 2026",
    timezone: "America/New_York (EST)",
    sendWindow: "Weekdays, 9:00 AM – 5:00 PM",
  },
};

export function getMockWorkflowReview(_workflowId: string): WorkflowReviewData {
  return mockWorkflowReview;
}
