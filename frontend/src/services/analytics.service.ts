import { apiClient } from "../api/client";

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
): Promise<WorkflowAnalytics> {
  const response = await apiClient<SuccessResponse<WorkflowAnalytics>>(
    `/api/v1/analytics/${workflowId}`,
  );
  return response.data;
}
