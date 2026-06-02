import { apiClient } from "../api/client";
import { parseWorkflowDefinition } from "../lib/parse-workflow-definition";
import type { BriefStatus, CampaignBrief } from "../types/campaign-brief";
import type { Recipient, RecipientCounts } from "../types/recipient";
import type { WorkflowDefinition } from "../types/workflow-definition";

interface SuccessResponse<T> {
  success: true;
  data: T;
}

export interface WorkflowRecord {
  id: string;
  name: string;
  status: string;
  activeVersion?: number | null;
  activatedAt?: string | null;
  createdAt: string;
}

export interface ActivateWorkflowResult {
  workflowId: string;
  status: string;
  activeVersion: number;
  activatedAt: string;
  executionsCreated: number;
  runsQueued: number;
  message: string;
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
  recipients?: Recipient[];
  recipientCounts?: RecipientCounts;
}

function normalizeWorkflowRecord(
  raw: WorkflowRecord & {
    created_at?: string;
    active_version?: number | null;
    activated_at?: string | null;
  },
): WorkflowRecord {
  return {
    id: raw.id,
    name: raw.name,
    status: raw.status,
    activeVersion: raw.activeVersion ?? raw.active_version,
    activatedAt: raw.activatedAt ?? raw.activated_at,
    createdAt: raw.createdAt ?? raw.created_at ?? "",
  };
}

export async function fetchWorkflows(): Promise<WorkflowRecord[]> {
  const response = await apiClient<SuccessResponse<WorkflowRecord[]>>(
    "/api/v1/workflows",
  );
  return (response.data ?? []).map((item) =>
    normalizeWorkflowRecord(item as WorkflowRecord & { created_at?: string }),
  );
}

export async function createWorkflow(name?: string): Promise<WorkflowRecord> {
  const response = await apiClient<SuccessResponse<WorkflowRecord>>(
    "/api/v1/workflows",
    {
      method: "POST",
      body: JSON.stringify({ name: name ?? undefined }),
    },
  );
  return normalizeWorkflowRecord(
    response.data as WorkflowRecord & { created_at?: string },
  );
}

export interface UpdateWorkflowStatusResult extends WorkflowRecord {
  runsEnqueued: number;
}

export async function updateWorkflowStatus(
  workflowId: string,
  status: "active" | "paused",
): Promise<UpdateWorkflowStatusResult> {
  const response = await apiClient<
    SuccessResponse<
      WorkflowRecord & {
        created_at?: string;
        runs_enqueued?: number;
        runsEnqueued?: number;
      }
    >
  >(`/api/v1/workflows/${encodeURIComponent(workflowId)}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  const raw = response.data;
  const record = normalizeWorkflowRecord(
    raw as WorkflowRecord & { created_at?: string },
  );
  return {
    ...record,
    runsEnqueued: raw.runsEnqueued ?? raw.runs_enqueued ?? 0,
  };
}

export interface RequeueWorkflowRunsResult {
  workflowId: string;
  runsEnqueued: number;
  message: string;
}

export async function requeueWorkflowRuns(
  workflowId: string,
): Promise<RequeueWorkflowRunsResult> {
  const response = await apiClient<
    SuccessResponse<{
      workflowId?: string;
      workflow_id?: string;
      runsEnqueued?: number;
      runs_enqueued?: number;
      message: string;
    }>
  >(`/api/v1/workflows/${encodeURIComponent(workflowId)}/runs/requeue`, {
    method: "POST",
  });
  const raw = response.data;
  return {
    workflowId: raw.workflowId ?? raw.workflow_id ?? workflowId,
    runsEnqueued: raw.runsEnqueued ?? raw.runs_enqueued ?? 0,
    message: raw.message,
  };
}

export async function activateWorkflow(workflowId: string): Promise<ActivateWorkflowResult> {
  const response = await apiClient<SuccessResponse<ActivateWorkflowResult & {
    workflow_id?: string;
    active_version?: number;
    activated_at?: string;
    executions_created?: number;
    runs_queued?: number;
  }>>(
    `/api/v1/workflows/${encodeURIComponent(workflowId)}/activate`,
    { method: "POST" },
  );
  const raw = response.data;
  return {
    workflowId: raw.workflowId ?? raw.workflow_id ?? workflowId,
    status: raw.status,
    activeVersion: raw.activeVersion ?? raw.active_version ?? 1,
    activatedAt: raw.activatedAt ?? raw.activated_at ?? "",
    executionsCreated: raw.executionsCreated ?? raw.executions_created ?? 0,
    runsQueued: raw.runsQueued ?? raw.runs_queued ?? 0,
    message: raw.message,
  };
}

export interface DeleteWorkflowResult {
  workflowId: string;
  message: string;
}

export async function deleteWorkflow(workflowId: string): Promise<DeleteWorkflowResult> {
  const response = await apiClient<
    SuccessResponse<{
      workflowId?: string;
      workflow_id?: string;
      message: string;
    }>
  >(`/api/v1/workflows/${encodeURIComponent(workflowId)}`, {
    method: "DELETE",
  });
  const raw = response.data;
  return {
    workflowId: raw.workflowId ?? raw.workflow_id ?? workflowId,
    message: raw.message,
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
    recipients: (data.recipients as Recipient[] | undefined) ?? [],
    recipientCounts:
      (data.recipientCounts as RecipientCounts | undefined) ??
      (data as { recipient_counts?: RecipientCounts }).recipient_counts,
  };
}
