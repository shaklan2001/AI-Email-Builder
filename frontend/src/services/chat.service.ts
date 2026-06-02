import { apiClient } from "../api/client";
import { parseWorkflowDefinition } from "../lib/parse-workflow-definition";
import type { BriefStatus, CampaignBrief } from "../types/campaign-brief";
import type { ReviewStatus } from "../types/workflow-review";
import type { WorkflowDefinition } from "../types/workflow-definition";

export interface SendChatMessageRequest {
  message: string;
  threadId: string;
}

export interface ChatApiPayload {
  message: string;
  stage: string;
  campaignBrief: CampaignBrief | null;
  workflowPreview: WorkflowDefinition | null;
  briefStatus: BriefStatus;
  reviewStatus: ReviewStatus;
  activationAllowed: boolean;
}

export interface ChatThreadPayload extends ChatApiPayload {
  threadId: string;
  messages: Array<{ role: string; content: string }>;
}

interface SuccessResponse<T> {
  success: true;
  data: T;
}

type RawChatData = {
  message?: string;
  stage?: string;
  campaignBrief?: CampaignBrief | null;
  campaign_brief?: CampaignBrief | null;
  workflowPreview?: WorkflowDefinition | null;
  workflow_preview?: WorkflowDefinition | null;
  workflow?: WorkflowDefinition | null;
  briefStatus?: BriefStatus;
  brief_status?: BriefStatus;
  reviewStatus?: ReviewStatus;
  review_status?: ReviewStatus;
  activationAllowed?: boolean;
  activation_allowed?: boolean;
};

type RawThreadData = RawChatData & {
  threadId?: string;
  thread_id?: string;
  messages?: Array<{ role: string; content: string }>;
};

function parseWorkflowPreview(raw: RawChatData): WorkflowDefinition | null {
  const candidate =
    raw.workflowPreview ??
    raw.workflow_preview ??
    raw.workflow ??
    null;
  if (!candidate) {
    return null;
  }
  return parseWorkflowDefinition(
    candidate as WorkflowDefinition & {
      workflow_type?: WorkflowDefinition["workflowType"];
    },
  );
}

function mapChatPayload(raw: RawChatData): ChatApiPayload {
  return {
    message: raw.message ?? "",
    stage: raw.stage ?? "CAMPAIGN_DISCOVERY",
    campaignBrief: (raw.campaignBrief ?? raw.campaign_brief ?? null) as CampaignBrief | null,
    workflowPreview: parseWorkflowPreview(raw),
    briefStatus: (raw.briefStatus ?? raw.brief_status ?? null) as BriefStatus,
    reviewStatus: (raw.reviewStatus ?? raw.review_status ?? null) as ReviewStatus,
    activationAllowed: Boolean(raw.activationAllowed ?? raw.activation_allowed),
  };
}

function mapThreadPayload(raw: RawThreadData): ChatThreadPayload {
  const base = mapChatPayload(raw);
  return {
    ...base,
    threadId: raw.threadId ?? raw.thread_id ?? "",
    messages: raw.messages ?? [],
  };
}

export type SendChatMessageResponse = ChatApiPayload;

export async function sendMessage(
  request: SendChatMessageRequest,
): Promise<SendChatMessageResponse> {
  const response = await apiClient<SuccessResponse<RawChatData>>(
    "/api/chat/message",
    {
      method: "POST",
      body: JSON.stringify({
        message: request.message,
        threadId: request.threadId,
      }),
    },
  );
  return mapChatPayload(response.data);
}

export async function fetchChatThread(threadId: string): Promise<ChatThreadPayload> {
  const response = await apiClient<SuccessResponse<RawThreadData>>(
    `/api/chat/thread/${encodeURIComponent(threadId)}`,
  );
  return mapThreadPayload(response.data);
}

export async function resetChatThread(threadId: string): Promise<ChatThreadPayload> {
  const response = await apiClient<SuccessResponse<RawThreadData>>("/api/chat/reset", {
    method: "POST",
    body: JSON.stringify({ threadId }),
  });
  return mapThreadPayload(response.data);
}
