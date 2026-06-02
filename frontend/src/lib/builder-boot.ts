import type { ChatMessage } from "../components/chat/types";
import { setStoredRecipients } from "../mocks/recipient-storage";
import {
  createEmptyCampaignMetadata,
  loadRecipientDraft,
} from "./workflow-persistence";
import type { ChatThreadPayload } from "../services/chat.service";
import type { WorkflowSession } from "../services/workflow.service";
import type { BriefStatus, CampaignBrief } from "../types/campaign-brief";
import type { ReviewStatus } from "../types/workflow-review";
import type { BuilderStage, CampaignMetadata } from "../types/workflow-draft";
import type { WorkflowDefinition } from "../types/workflow-definition";

export interface BuilderBootState {
  stage: BuilderStage;
  firstPrompt: string | null;
  showPrompt: boolean;
  showBuilder: boolean;
  initialMessages: ChatMessage[] | undefined;
  initialWorkflowDefinition: WorkflowDefinition | null;
  initialCampaignBrief: CampaignBrief | null;
  initialBriefStatus: BriefStatus;
  initialReviewStatus: ReviewStatus;
  initialActivationAllowed: boolean;
  campaign: CampaignMetadata;
  layoutKey: number;
}

function messagesFromRows(
  rows: Array<{ role: string; content: string }>,
  idPrefix: string,
): ChatMessage[] | undefined {
  if (rows.length === 0) {
    return undefined;
  }
  return rows.map((m, index) => ({
    id: `${idPrefix}-${index}-${m.role}`,
    role: m.role as "user" | "assistant",
    content: m.content,
  }));
}

function messagesFromSession(
  session: WorkflowSession,
): ChatMessage[] | undefined {
  return messagesFromRows(session.messages, "session");
}

function messagesFromChatThread(
  thread: ChatThreadPayload,
): ChatMessage[] | undefined {
  return messagesFromRows(thread.messages, "thread");
}

function bootFromChatThread(
  thread: ChatThreadPayload,
  startAtPrompt: boolean,
): BuilderBootState {
  const messages = messagesFromChatThread(thread);
  const hasConversation = Boolean(messages && messages.length > 0);
  const firstUser = messages?.find((m) => m.role === "user");
  const inBuilder =
    hasConversation || Boolean(thread.workflowPreview?.steps?.length);

  if (startAtPrompt && !inBuilder) {
    const campaign = createEmptyCampaignMetadata(true);
    return {
      stage: "prompt",
      firstPrompt: null,
      showPrompt: true,
      showBuilder: false,
      initialMessages: undefined,
      initialWorkflowDefinition: null,
      initialCampaignBrief: null,
      initialBriefStatus: null,
      initialReviewStatus: null,
      initialActivationAllowed: false,
      campaign,
      layoutKey: 0,
    };
  }

  return {
    stage: "builder",
    firstPrompt: firstUser?.content ?? null,
    showPrompt: false,
    showBuilder: true,
    initialMessages: messages,
    initialWorkflowDefinition: thread.workflowPreview,
    initialCampaignBrief: thread.campaignBrief,
    initialBriefStatus: thread.briefStatus,
    initialReviewStatus: thread.reviewStatus,
    initialActivationAllowed: thread.activationAllowed,
    campaign: {
      firstPrompt: firstUser?.content ?? null,
      builderStage: "builder",
    },
    layoutKey: 0,
  };
}

function hydrateRecipientsFromSession(session: WorkflowSession, workflowId: string): void {
  const items = session.recipients ?? [];
  const counts = session.recipientCounts;
  if (items.length > 0 || (counts && counts.validCount > 0)) {
    setStoredRecipients(
      workflowId,
      items,
      counts?.invalidCount ?? 0,
    );
  }
}

function bootFromSession(
  session: WorkflowSession,
  startAtPrompt: boolean,
  workflowId: string,
): BuilderBootState {
  hydrateRecipientsFromSession(session, workflowId);
  const messages = messagesFromSession(session);
  const hasConversation = Boolean(messages && messages.length > 0);
  const firstUser = messages?.find((m) => m.role === "user");
  const inBuilder = hasConversation || Boolean(session.workflow?.steps?.length);

  if (startAtPrompt && !inBuilder) {
    const campaign = createEmptyCampaignMetadata(true);
    return {
      stage: "prompt",
      firstPrompt: null,
      showPrompt: true,
      showBuilder: false,
      initialMessages: undefined,
      initialWorkflowDefinition: null,
      initialCampaignBrief: null,
      initialBriefStatus: null,
      initialReviewStatus: null,
      initialActivationAllowed: false,
      campaign,
      layoutKey: 0,
    };
  }

  return {
    stage: "builder",
    firstPrompt: firstUser?.content ?? null,
    showPrompt: false,
    showBuilder: true,
    initialMessages: messages,
    initialWorkflowDefinition: session.workflow,
    initialCampaignBrief: session.campaignBrief,
    initialBriefStatus: session.briefStatus,
    initialReviewStatus: null,
    initialActivationAllowed: false,
    campaign: {
      firstPrompt: firstUser?.content ?? null,
      builderStage: "builder",
    },
    layoutKey: 0,
  };
}

function bootFromDraft(workflowId: string): BuilderBootState | null {
  const draft = loadRecipientDraft(workflowId);
  if (!draft) {
    return null;
  }

  setStoredRecipients(
    workflowId,
    draft.recipients,
    draft.invalidRecipientCount,
  );

  return null;
}

/** Restore recipient counts from local draft only; conversation state comes from the API. */
function hydrateRecipientsFromDraft(workflowId: string): void {
  const draft = loadRecipientDraft(workflowId);
  if (!draft) {
    return;
  }
  setStoredRecipients(
    workflowId,
    draft.recipients,
    draft.invalidRecipientCount,
  );
}

export function buildBuilderBoot(
  workflowId: string,
  options: { startAtPrompt: boolean },
  session?: WorkflowSession | null,
  chatThread?: ChatThreadPayload | null,
): BuilderBootState {
  hydrateRecipientsFromDraft(workflowId);

  // MongoDB conversation state is the source of truth (spec 33).
  if (chatThread) {
    return bootFromChatThread(chatThread, options.startAtPrompt);
  }

  if (session) {
    return bootFromSession(session, options.startAtPrompt, workflowId);
  }

  const fromDraft = bootFromDraft(workflowId);
  if (fromDraft) {
    return fromDraft;
  }

  const campaign = createEmptyCampaignMetadata(options.startAtPrompt);
  return {
    stage: campaign.builderStage,
    firstPrompt: null,
    showPrompt: options.startAtPrompt,
    showBuilder: !options.startAtPrompt,
    initialMessages: undefined,
    initialWorkflowDefinition: null,
    initialCampaignBrief: null,
    initialBriefStatus: null,
    initialReviewStatus: null,
    initialActivationAllowed: false,
    campaign,
    layoutKey: 0,
  };
}
