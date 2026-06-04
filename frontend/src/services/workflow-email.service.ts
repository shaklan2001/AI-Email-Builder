import { apiClient } from "../api/client";
import { parseWorkflowDefinition } from "../lib/parse-workflow-definition";
import type { WorkflowDefinition } from "../types/workflow-definition";

export interface UpdateWorkflowEmailRequest {
  subject: string;
  htmlContent: string;
  plainTextContent: string;
}

interface SuccessResponse<T> {
  success: true;
  data: T;
}

export async function updateWorkflowEmail(
  workflowId: string,
  stepId: string,
  body: UpdateWorkflowEmailRequest,
): Promise<WorkflowDefinition> {
  const response = await apiClient<
    SuccessResponse<WorkflowDefinition & { workflow_type?: WorkflowDefinition["workflowType"] }>
  >(`/api/v1/workflows/${workflowId}/emails/${stepId}`, {
    method: "PATCH",
    body: JSON.stringify({
      subject: body.subject,
      htmlContent: body.htmlContent,
      plainTextContent: body.plainTextContent,
    }),
  });

  const workflow = parseWorkflowDefinition(response.data);
  if (!workflow) {
    throw new Error("Invalid workflow response from server");
  }
  return workflow;
}
