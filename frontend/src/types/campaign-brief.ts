export interface CampaignBrief {
  campaignName?: string | null;
  businessGoal?: string | null;
  audience?: string | null;
  productInfo?: string | null;
  tone?: string | null;
  cta?: string | null;
  attachments?: string | null;
  landingPage?: string | null;
  followUpStrategy?: string | null;
  replyStrategy?: string | null;
}

export type BriefStatus = "pending_approval" | "approved" | "editing" | null;
