import type { ChatMessage } from "../components/chat/types";
import type { BriefStatus, CampaignBrief } from "../types/campaign-brief";
import type { Recipient } from "../types/recipient";
import type {
  CampaignMetadata,
  WorkflowDraft,
} from "../types/workflow-draft";
import type { WorkflowDefinition } from "../types/workflow-definition";
import type { WorkflowState } from "../types/workflow-state";

const STORAGE_PREFIX = "workflow-draft:";
export const WORKFLOW_DRAFT_VERSION = 1 as const;

function getStorageKey(workflowId: string): string {
  return `${STORAGE_PREFIX}${workflowId}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isValidChatMessage(value: unknown): value is ChatMessage {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.id === "string" &&
    (value.role === "user" || value.role === "assistant") &&
    typeof value.content === "string" &&
    (value.isLoading === undefined || typeof value.isLoading === "boolean") &&
    (value.isPlaceholder === undefined || typeof value.isPlaceholder === "boolean")
  );
}

/** Strip legacy placeholder rows and in-flight loading bubbles from persisted chat. */
export function sanitizeChatMessages(messages: ChatMessage[]): ChatMessage[] {
  return messages.filter((message) => {
    const legacy = message as ChatMessage & { isPlaceholder?: boolean };
    return !legacy.isPlaceholder && !message.isLoading;
  });
}

function isValidWorkflowDefinition(value: unknown): value is WorkflowDefinition {
  if (!isRecord(value)) {
    return false;
  }

  if (!Array.isArray(value.steps)) {
    return false;
  }

  return value.steps.every((step) => {
    if (!isRecord(step)) {
      return false;
    }
    return typeof step.id === "string" && typeof step.type === "string";
  });
}

function isValidWorkflowState(value: unknown): value is WorkflowState {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.initialEmailLabel === "string" &&
    typeof value.waitLabel === "string" &&
    typeof value.conditionLabel === "string" &&
    typeof value.yesBranchLabel === "string" &&
    typeof value.noBranchLabel === "string" &&
    Array.isArray(value.extraSteps) &&
    value.extraSteps.every((step) => typeof step === "string")
  );
}

function isValidRecipient(value: unknown): value is Recipient {
  if (!isRecord(value)) {
    return false;
  }

  return typeof value.id === "string" && typeof value.email === "string";
}

function isValidBriefStatus(value: unknown): value is BriefStatus {
  return (
    value === null ||
    value === "pending_approval" ||
    value === "approved" ||
    value === "editing"
  );
}

function isValidCampaignBrief(value: unknown): value is CampaignBrief | null {
  if (value === null || value === undefined) {
    return true;
  }
  return isRecord(value);
}

function isValidCampaignMetadata(value: unknown): value is CampaignMetadata {
  if (!isRecord(value)) {
    return false;
  }

  const firstPrompt = value.firstPrompt;
  const builderStage = value.builderStage;

  return (
    (firstPrompt === null || typeof firstPrompt === "string") &&
    (builderStage === "prompt" || builderStage === "builder")
  );
}

function isValidWorkflowDraft(data: unknown, workflowId: string): data is WorkflowDraft {
  if (!isRecord(data)) {
    return false;
  }

  if (
    data.version !== WORKFLOW_DRAFT_VERSION ||
    data.workflowId !== workflowId ||
    typeof data.updatedAt !== "string" ||
    !isValidWorkflowState(data.workflow) ||
    (data.workflowDefinition !== undefined &&
      data.workflowDefinition !== null &&
      !isValidWorkflowDefinition(data.workflowDefinition)) ||
    !Array.isArray(data.messages) ||
    !data.messages.every(isValidChatMessage) ||
    !isValidCampaignMetadata(data.campaign) ||
    !Array.isArray(data.recipients) ||
    !data.recipients.every(isValidRecipient) ||
    typeof data.invalidRecipientCount !== "number" ||
    data.invalidRecipientCount < 0 ||
    !Number.isInteger(data.invalidRecipientCount) ||
    !isValidCampaignBrief(data.campaignBrief) ||
    !isValidBriefStatus(data.briefStatus ?? null)
  ) {
    return false;
  }

  return true;
}

export function loadWorkflowDraft(workflowId: string): WorkflowDraft | null {
  try {
    const raw = localStorage.getItem(getStorageKey(workflowId));
    if (!raw) {
      return null;
    }

    const parsed: unknown = JSON.parse(raw);
    if (!isValidWorkflowDraft(parsed, workflowId)) {
      clearWorkflowDraft(workflowId);
      return null;
    }

    return {
      ...parsed,
      messages: sanitizeChatMessages(parsed.messages),
    };
  } catch {
    clearWorkflowDraft(workflowId);
    return null;
  }
}

export function hasWorkflowDraft(workflowId: string): boolean {
  return loadWorkflowDraft(workflowId) !== null;
}

export interface SaveWorkflowDraftInput {
  workflowId: string;
  workflow: WorkflowState;
  workflowDefinition?: WorkflowDefinition | null;
  messages: ChatMessage[];
  campaign: CampaignMetadata;
  recipients: Recipient[];
  invalidRecipientCount: number;
  campaignBrief?: CampaignBrief | null;
  briefStatus?: BriefStatus;
}

export function saveWorkflowDraft(input: SaveWorkflowDraftInput): void {
  const draft: WorkflowDraft = {
    version: WORKFLOW_DRAFT_VERSION,
    workflowId: input.workflowId,
    workflow: input.workflow,
    workflowDefinition: input.workflowDefinition ?? null,
    messages: input.messages,
    campaign: input.campaign,
    recipients: input.recipients,
    invalidRecipientCount: input.invalidRecipientCount,
    campaignBrief: input.campaignBrief ?? null,
    briefStatus: input.briefStatus ?? null,
    updatedAt: new Date().toISOString(),
  };

  try {
    localStorage.setItem(getStorageKey(input.workflowId), JSON.stringify(draft));
  } catch {
    // Quota or private mode — fail silently per local-only MVP
  }
}

export function clearWorkflowDraft(workflowId: string): void {
  try {
    localStorage.removeItem(getStorageKey(workflowId));
  } catch {
    // ignore
  }
}

export function createEmptyCampaignMetadata(
  isNewWorkflow: boolean,
): CampaignMetadata {
  return {
    firstPrompt: null,
    builderStage: isNewWorkflow ? "prompt" : "builder",
  };
}

