export const queryKeys = {
  workflows: ["workflows"] as const,
  workflow: (id: string) => ["workflow", id] as const,
  workflowSession: (id: string) => ["workflow", id, "session"] as const,
  campaignBrief: (id: string) => ["workflow", id, "campaign-brief"] as const,
  workflowPreview: (id: string) => ["workflow", id, "workflow-preview"] as const,
  generatedEmails: (id: string) => ["workflow", id, "generated-emails"] as const,
  analytics: (id: string) => ["analytics", id] as const,
};
