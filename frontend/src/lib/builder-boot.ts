import type { ChatMessage } from "../components/chat/types";
import { setStoredRecipients } from "../mocks/recipient-storage";
import {
  createEmptyCampaignMetadata,
  loadWorkflowDraft,
} from "./workflow-persistence";
import type { WorkflowSession } from "../services/workflow.service";
import type { BriefStatus, CampaignBrief } from "../types/campaign-brief";
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
  campaign: CampaignMetadata;
  layoutKey: number;
}

function messagesFromSession(
  session: WorkflowSession,
): ChatMessage[] | undefined {
  const rows = session.messages;
  if (rows.length === 0) {
    return undefined;
  }
  return rows.map((m, index) => ({
    id: `session-${index}-${m.role}`,
    role: m.role as "user" | "assistant",
    content: m.content,
  }));
}

function bootFromSession(
  session: WorkflowSession,
  startAtPrompt: boolean,
): BuilderBootState {
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
    campaign: {
      firstPrompt: firstUser?.content ?? null,
      builderStage: "builder",
    },
    layoutKey: 0,
  };
}

function bootFromDraft(
  workflowId: string,
  isNewRoute: boolean,
): BuilderBootState | null {
  const draft = loadWorkflowDraft(workflowId);
  if (!draft) {
    return null;
  }

  setStoredRecipients(
    workflowId,
    draft.recipients,
    draft.invalidRecipientCount,
  );

  const stage = draft.campaign.builderStage;
  const inBuilder = stage === "builder";

  return {
    stage,
    firstPrompt: draft.campaign.firstPrompt,
    showPrompt: isNewRoute && !inBuilder,
    showBuilder: !isNewRoute || inBuilder,
    initialMessages: draft.messages,
    initialWorkflowDefinition: draft.workflowDefinition ?? null,
    initialCampaignBrief: draft.campaignBrief ?? null,
    initialBriefStatus: draft.briefStatus ?? null,
    campaign: draft.campaign,
    layoutKey: 0,
  };
}

export function buildBuilderBoot(
  workflowId: string,
  options: { startAtPrompt: boolean },
  session?: WorkflowSession | null,
): BuilderBootState {
  const fromDraft = bootFromDraft(workflowId, options.startAtPrompt);
  if (fromDraft) {
    return fromDraft;
  }

  if (session) {
    return bootFromSession(session, options.startAtPrompt);
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
    campaign,
    layoutKey: 0,
  };
}
