export const LEAD_STATUSES = [
  "NEW",
  "EMAIL_SENT",
  "OPENED",
  "CLICKED",
  "REPLIED",
  "INTERESTED",
  "DEMO_BOOKED",
  "NOT_INTERESTED",
  "UNSUBSCRIBED",
  "CLOSED",
] as const;

export type LeadStatus = (typeof LEAD_STATUSES)[number];

export const leadStatusLabels: Record<LeadStatus, string> = {
  NEW: "New",
  EMAIL_SENT: "Email Sent",
  OPENED: "Opened",
  CLICKED: "Clicked",
  REPLIED: "Replied",
  INTERESTED: "Interested",
  DEMO_BOOKED: "Demo Booked",
  NOT_INTERESTED: "Not Interested",
  UNSUBSCRIBED: "Unsubscribed",
  CLOSED: "Closed",
};
