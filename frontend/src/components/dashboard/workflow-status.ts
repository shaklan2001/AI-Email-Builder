import type { WorkflowStatus } from "../../types/workflow";

export const statusLabels: Record<WorkflowStatus, string> = {
  draft: "Draft",
  generating: "Generating",
  awaiting_approval: "Awaiting Approval",
  active: "Active",
  paused: "Paused",
  completed: "Completed",
};

export const statusColors: Record<
  WorkflowStatus,
  "default" | "primary" | "success" | "warning" | "info"
> = {
  draft: "default",
  generating: "info",
  awaiting_approval: "warning",
  active: "success",
  paused: "default",
  completed: "success",
};

export function workflowStatusLabel(status: string): string {
  return status in statusLabels
    ? statusLabels[status as WorkflowStatus]
    : status.replace(/_/g, " ");
}

export function workflowStatusColor(
  status: string,
): "default" | "primary" | "success" | "warning" | "info" {
  return status in statusColors
    ? statusColors[status as WorkflowStatus]
    : "default";
}
