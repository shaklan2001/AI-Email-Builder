export type WorkflowStatus =
  | "draft"
  | "generating"
  | "awaiting_approval"
  | "active"
  | "paused"
  | "completed";

export interface MockWorkflow {
  id: string;
  name: string;
  status: WorkflowStatus;
  createdAt: string;
}

export const mockWorkflows: MockWorkflow[] = [
  {
    id: "wf_1",
    name: "Welcome Series",
    status: "active",
    createdAt: "2026-05-12T10:30:00.000Z",
  },
  {
    id: "wf_2",
    name: "Product Launch Announcement",
    status: "draft",
    createdAt: "2026-05-28T14:15:00.000Z",
  },
  {
    id: "wf_3",
    name: "Re-engagement Campaign",
    status: "awaiting_approval",
    createdAt: "2026-06-01T09:00:00.000Z",
  },
];
