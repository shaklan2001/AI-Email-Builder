import { apiClient } from "../api/client";
import type { ApiRequestOptions } from "../api/request-options";
import type {
  ConversationMessageType,
  ConversationThreadMessage,
} from "../types/conversation-thread";

interface SuccessResponse<T> {
  success: true;
  data: T;
}

export interface ConversationThreadSummary {
  leadEmail: string;
  messages: ConversationThreadMessage[];
  autoReplyCount: number;
  humanReviewRequired: boolean;
}

function normalizeMessageType(raw: string): ConversationMessageType {
  if (
    raw === "agent_message" ||
    raw === "prospect_reply" ||
    raw === "agent_response"
  ) {
    return raw;
  }
  return "agent_message";
}

function normalizeThread(raw: {
  leadEmail?: string;
  lead_email?: string;
  messages?: Array<{ id?: string; type?: string; content?: string }>;
  autoReplyCount?: number;
  auto_reply_count?: number;
  humanReviewRequired?: boolean;
  human_review_required?: boolean;
}): ConversationThreadSummary {
  const messages = (raw.messages ?? [])
    .filter((m) => m.content && m.content.trim())
    .map((m, index) => ({
      id: m.id ?? `msg-${index}`,
      type: normalizeMessageType(m.type ?? "agent_message"),
      content: m.content!.trim(),
    }));

  return {
    leadEmail: raw.leadEmail ?? raw.lead_email ?? "",
    messages,
    autoReplyCount: raw.autoReplyCount ?? raw.auto_reply_count ?? 0,
    humanReviewRequired:
      raw.humanReviewRequired ?? raw.human_review_required ?? false,
  };
}

export async function fetchConversationThreadPreview(
  campaignId: string,
  options?: ApiRequestOptions,
): Promise<ConversationThreadSummary | null> {
  const response = await apiClient<
    SuccessResponse<ConversationThreadSummary | null>
  >(
    `/api/v1/workflows/${encodeURIComponent(campaignId)}/conversation-threads/preview`,
    options,
  );

  if (!response.data) {
    return null;
  }
  return normalizeThread(response.data);
}

export async function fetchConversationThreads(
  campaignId: string,
): Promise<ConversationThreadSummary[]> {
  const response = await apiClient<SuccessResponse<ConversationThreadSummary[]>>(
    `/api/v1/workflows/${encodeURIComponent(campaignId)}/conversation-threads`,
  );
  return (response.data ?? []).map(normalizeThread);
}
