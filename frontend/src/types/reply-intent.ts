export const REPLY_INTENTS = [
  "COMPANY_INFO",
  "DEMO_REQUEST",
  "PRICING",
  "INTERESTED",
  "NOT_INTERESTED",
  "UNSUBSCRIBE",
  "UNKNOWN",
] as const;

export type ReplyIntent = (typeof REPLY_INTENTS)[number];

export const replyIntentLabels: Record<ReplyIntent, string> = {
  COMPANY_INFO: "Company Info",
  DEMO_REQUEST: "Demo Request",
  PRICING: "Pricing",
  INTERESTED: "Interested",
  NOT_INTERESTED: "Not Interested",
  UNSUBSCRIBE: "Unsubscribe",
  UNKNOWN: "Unknown",
};
