import { apiClient } from "../api/client";
import { parseWorkflowDefinition } from "../lib/parse-workflow-definition";
import type { BriefStatus, CampaignBrief } from "../types/campaign-brief";
import type { WorkflowDefinition } from "../types/workflow-definition";

interface SuccessResponse<T> {
  success: true;
  data: T;
}

export interface WorkflowRecord {
  id: string;
  name: string;
  status: string;
  createdAt: string;
}

export interface CampaignDraft {
  campaignName?: string | null;
  businessGoal?: string | null;
  productInfo?: string | null;
  audience?: string | null;
  tone?: string | null;
  cta?: string | null;
  landingPage?: string | null;
  productImage?: string | null;
  followUpStrategy?: string | null;
  replyStrategy?: string | null;
}

export interface WorkflowSession {
  messages: Array<{ role: string; content: string }>;
  campaignDraft: CampaignDraft;
  campaignBrief: CampaignBrief | null;
  briefStatus: BriefStatus;
  workflow: WorkflowDefinition | null;
  generatedEmails: unknown[];
}

export async function createWorkflow(name?: string): Promise<WorkflowRecord> {
  const response = await apiClient<SuccessResponse<WorkflowRecord>>(
    "/api/v1/workflows",
    {
      method: "POST",
      body: JSON.stringify({ name: name ?? undefined }),
    },
  );
  const raw = response.data as WorkflowRecord & { created_at?: string };
  return {
    id: raw.id,
    name: raw.name,
    status: raw.status,
    createdAt: raw.createdAt ?? raw.created_at ?? "",
  };
}

export async function fetchWorkflowSession(workflowId: string): Promise<WorkflowSession> {
  const response = await apiClient<SuccessResponse<WorkflowSession>>(
    `/api/v1/workflows/${workflowId}/session`,
  );
  const data = response.data;
  const rawWorkflow = data.workflow as
    | (WorkflowDefinition & { workflow_type?: WorkflowDefinition["workflowType"] })
    | null
    | undefined;

  return {
    messages: data.messages ?? [],
    campaignDraft: data.campaignDraft ?? {},
    campaignBrief: (data.campaignBrief as CampaignBrief | null) ?? null,
    briefStatus: (data.briefStatus as BriefStatus) ?? null,
    workflow: parseWorkflowDefinition(rawWorkflow),
    generatedEmails: data.generatedEmails ?? [],
  };
}
