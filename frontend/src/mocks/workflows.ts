import type { WorkflowStatus } from "../types/workflow";

export type { WorkflowStatus };

/** @deprecated Dashboard uses GET /api/v1/workflows. Kept for local UI experiments only. */
export interface MockWorkflow {
  id: string;
  name: string;
  status: WorkflowStatus;
  createdAt: string;
}

/** @deprecated Use fetchWorkflows() instead. */
export const mockWorkflows: MockWorkflow[] = [];
