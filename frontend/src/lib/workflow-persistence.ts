import type { ChatMessage } from "../components/chat/types";
import type { Recipient } from "../types/recipient";

const STORAGE_PREFIX = "workflow-recipients:";
export const RECIPIENT_DRAFT_VERSION = 1 as const;

/** Strip legacy placeholder rows and in-flight loading bubbles from persisted chat. */
export function sanitizeChatMessages(messages: ChatMessage[]): ChatMessage[] {
  return messages.filter((message) => {
    const legacy = message as ChatMessage & { isPlaceholder?: boolean };
    return !legacy.isPlaceholder && !message.isLoading;
  });
}

export interface RecipientDraft {
  version: typeof RECIPIENT_DRAFT_VERSION;
  workflowId: string;
  recipients: Recipient[];
  invalidRecipientCount: number;
  updatedAt: string;
}

function getStorageKey(workflowId: string): string {
  return `${STORAGE_PREFIX}${workflowId}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isValidRecipient(value: unknown): value is Recipient {
  if (!isRecord(value)) {
    return false;
  }
  return typeof value.id === "string" && typeof value.email === "string";
}

function isValidRecipientDraft(data: unknown, workflowId: string): data is RecipientDraft {
  if (!isRecord(data)) {
    return false;
  }
  return (
    data.version === RECIPIENT_DRAFT_VERSION &&
    data.workflowId === workflowId &&
    typeof data.updatedAt === "string" &&
    Array.isArray(data.recipients) &&
    data.recipients.every(isValidRecipient) &&
    typeof data.invalidRecipientCount === "number" &&
    data.invalidRecipientCount >= 0 &&
    Number.isInteger(data.invalidRecipientCount)
  );
}

/** Load locally cached recipients only — chat/workflow state comes from the API. */
export function loadRecipientDraft(workflowId: string): RecipientDraft | null {
  try {
    const raw = localStorage.getItem(getStorageKey(workflowId));
    if (!raw) {
      return null;
    }
    const parsed: unknown = JSON.parse(raw);
    if (!isValidRecipientDraft(parsed, workflowId)) {
      clearRecipientDraft(workflowId);
      return null;
    }
    return parsed;
  } catch {
    clearRecipientDraft(workflowId);
    return null;
  }
}

export function saveRecipientDraft(input: {
  workflowId: string;
  recipients: Recipient[];
  invalidRecipientCount: number;
}): void {
  const draft: RecipientDraft = {
    version: RECIPIENT_DRAFT_VERSION,
    workflowId: input.workflowId,
    recipients: input.recipients,
    invalidRecipientCount: input.invalidRecipientCount,
    updatedAt: new Date().toISOString(),
  };
  try {
    localStorage.setItem(getStorageKey(input.workflowId), JSON.stringify(draft));
  } catch {
    // Quota or private mode — fail silently
  }
}

export function clearRecipientDraft(workflowId: string): void {
  try {
    localStorage.removeItem(getStorageKey(workflowId));
  } catch {
    // ignore
  }
}

/** @deprecated Use loadRecipientDraft — kept for migration from workflow-draft:* keys. */
export function loadWorkflowDraft(workflowId: string): {
  recipients: Recipient[];
  invalidRecipientCount: number;
} | null {
  const draft = loadRecipientDraft(workflowId);
  if (draft) {
    return {
      recipients: draft.recipients,
      invalidRecipientCount: draft.invalidRecipientCount,
    };
  }
  try {
    const legacyRaw = localStorage.getItem(`workflow-draft:${workflowId}`);
    if (!legacyRaw) {
      return null;
    }
    const parsed: unknown = JSON.parse(legacyRaw);
    if (!isRecord(parsed) || parsed.workflowId !== workflowId) {
      return null;
    }
    const recipients = parsed.recipients;
    const invalid = parsed.invalidRecipientCount;
    if (!Array.isArray(recipients) || typeof invalid !== "number") {
      return null;
    }
    const validRecipients = recipients.filter(isValidRecipient);
    return {
      recipients: validRecipients,
      invalidRecipientCount: invalid,
    };
  } catch {
    return null;
  }
}

export function clearWorkflowDraft(workflowId: string): void {
  clearRecipientDraft(workflowId);
  try {
    localStorage.removeItem(`workflow-draft:${workflowId}`);
  } catch {
    // ignore
  }
}

export function createEmptyCampaignMetadata(isNewWorkflow: boolean): {
  firstPrompt: string | null;
  builderStage: "prompt" | "builder";
} {
  return {
    firstPrompt: null,
    builderStage: isNewWorkflow ? "prompt" : "builder",
  };
}
