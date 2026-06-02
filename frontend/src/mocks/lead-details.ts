import type { LeadDetails } from "../types/lead-details";

export const mockLeadDetails: LeadDetails[] = [
  {
    email: "alex.chen@acmecorp.com",
    name: "Alex Chen",
    intent: "DEMO_REQUEST",
  },
  {
    email: "jordan.lee@startup.io",
    name: "Jordan Lee",
    intent: "PRICING",
  },
  {
    email: "sam.patel@enterprise.com",
    name: "Sam Patel",
    intent: "INTERESTED",
  },
  {
    email: "taylor.wright@company.net",
    name: "Taylor Wright",
  },
  {
    email: "casey.morgan@business.co",
    intent: "NOT_INTERESTED",
  },
];

export function getMockLeadDetails(_workflowId: string): LeadDetails[] {
  return mockLeadDetails;
}
