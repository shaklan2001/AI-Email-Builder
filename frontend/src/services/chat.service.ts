import { apiClient } from "../api/client";
import { parseWorkflowDefinition } from "../lib/parse-workflow-definition";
import type { BriefStatus, CampaignBrief } from "../types/campaign-brief";
import type { WorkflowDefinition } from "../types/workflow-definition";

export interface SendChatMessageRequest {
  message: string;
  workflowId: string;
}

export interface SendChatMessageResponse {
  message: string;
  workflow: WorkflowDefinition | null;
  campaignBrief: CampaignBrief | null;
  briefStatus: BriefStatus;
}

interface SuccessResponse<T> {
  success: true;
  data: T;
}

export async function sendMessage(
  request: SendChatMessageRequest,
): Promise<SendChatMessageResponse> {
  const response = await apiClient<SuccessResponse<SendChatMessageResponse>>(
    "/api/v1/chat/message",
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
  const data = response.data;
  const rawWorkflow = data.workflow as
    | (WorkflowDefinition & { workflow_type?: WorkflowDefinition["workflowType"] })
    | null
    | undefined;

  const rawBrief = data.campaignBrief as CampaignBrief | null | undefined;

  return {
    message: data.message ?? "",
    campaignBrief: rawBrief ?? null,
    briefStatus: (data.briefStatus as BriefStatus) ?? null,
    workflow: parseWorkflowDefinition(rawWorkflow),
  };
}
