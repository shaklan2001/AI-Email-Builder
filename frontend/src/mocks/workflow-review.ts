import { mockLeadDetails } from "./lead-details";
import type { LeadStatusCounts, WorkflowReviewData } from "../types/workflow-review";

const mockLeadStatusCounts: LeadStatusCounts = {
  NEW: 24,
  EMAIL_SENT: 38,
  OPENED: 22,
  CLICKED: 9,
  REPLIED: 12,
  INTERESTED: 6,
  DEMO_BOOKED: 3,
  NOT_INTERESTED: 5,
  UNSUBSCRIBED: 2,
  CLOSED: 7,
};

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
  leadStatusCounts: mockLeadStatusCounts,
  leadDetails: mockLeadDetails,
};

export function getMockWorkflowReview(_workflowId: string): WorkflowReviewData {
  return mockWorkflowReview;
}
