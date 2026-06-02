export interface CampaignBrief {
  campaignName?: string | null;
  productInfo?: string | null;
  audience?: string | null;
  cta?: string | null;
  tone?: string | null;
  landingPage?: string | null;
  imageUrl?: string | null;
  emailLength?: string | null;
  followUpEnabled?: string | null;
  followUpDelay?: string | null;
  replyHandling?: string | null;
  toolsAvailable?: string[];
}

export type BriefStatus = "pending_approval" | "approved" | "editing" | null;

export const DEFAULT_TOOLS_AVAILABLE = [
  "Company Information",
  "Demo Booking",
] as const;
