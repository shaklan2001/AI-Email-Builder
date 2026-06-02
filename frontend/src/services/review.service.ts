import { apiClient } from "../api/client";
import type { WorkflowReviewData } from "../types/workflow-review";

interface SuccessResponse<T> {
  success: true;
  data: T;
}

export async function fetchWorkflowReview(
  workflowId: string,
): Promise<WorkflowReviewData> {
  const response = await apiClient<SuccessResponse<WorkflowReviewData>>(
    `/api/v1/review/${workflowId}`,
  );
  return response.data;
}

export async function approveWorkflowReview(
  workflowId: string,
): Promise<WorkflowReviewData> {
  const response = await apiClient<SuccessResponse<WorkflowReviewData>>(
    `/api/v1/review/${workflowId}/approve`,
    { method: "POST" },
  );
  return response.data;
}
