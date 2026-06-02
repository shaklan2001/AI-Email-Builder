import type { ChatMessage } from "../components/chat/types";
import type { BriefStatus, CampaignBrief } from "./campaign-brief";
import type { FollowUpDelay } from "./follow-up-delay";
import type { Recipient } from "./recipient";
import type { WorkflowDefinition } from "./workflow-definition";
import type { WorkflowState } from "./workflow-state";

export type BuilderStage = "prompt" | "builder";

export interface CampaignMetadata {
  firstPrompt: string | null;
  builderStage: BuilderStage;
}

export interface WorkflowDraft {
  version: 1;
  workflowId: string;
  workflow: WorkflowState;
  followUpDelay?: FollowUpDelay | null;
  workflowDefinition?: WorkflowDefinition | null;
  messages: ChatMessage[];
  campaign: CampaignMetadata;
  recipients: Recipient[];
  invalidRecipientCount: number;
  campaignBrief?: CampaignBrief | null;
  briefStatus?: BriefStatus;
  updatedAt: string;
}

export type DraftSaveStatus = "idle" | "saving" | "saved";
