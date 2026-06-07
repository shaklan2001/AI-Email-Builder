import { apiClient } from "../api/client";
import type { ApiRequestOptions } from "../api/request-options";

interface SuccessResponse<T> {
  success: true;
  data: T;
}

export interface WorkflowAnalytics {
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  replied: number;
  failed: number;
  bounced: number;
}

export async function fetchWorkflowAnalytics(
  workflowId: string,
  options?: ApiRequestOptions,
): Promise<WorkflowAnalytics> {
  const response = await apiClient<SuccessResponse<WorkflowAnalytics>>(
    `/api/v1/analytics/${workflowId}`,
    options,
  );
  return response.data;
}
