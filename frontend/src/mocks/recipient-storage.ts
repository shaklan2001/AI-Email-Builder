import type { Recipient, RecipientCounts } from "../types/recipient";

const recipientsByWorkflow = new Map<string, Recipient[]>();
const invalidCountByWorkflow = new Map<string, number>();

export function getStoredRecipients(workflowId: string): Recipient[] {
  return recipientsByWorkflow.get(workflowId) ?? [];
}

export function getRecipientCounts(workflowId: string): RecipientCounts {
  return {
    validCount: getStoredRecipients(workflowId).length,
    invalidCount: invalidCountByWorkflow.get(workflowId) ?? 0,
  };
}

export function addValidRecipients(workflowId: string, recipients: Recipient[]): RecipientCounts {
  const existing = getStoredRecipients(workflowId);
  recipientsByWorkflow.set(workflowId, [...existing, ...recipients]);
  return getRecipientCounts(workflowId);
}

export function addInvalidCount(workflowId: string, count: number): RecipientCounts {
  const current = invalidCountByWorkflow.get(workflowId) ?? 0;
  invalidCountByWorkflow.set(workflowId, current + count);
  return getRecipientCounts(workflowId);
}

export function setStoredRecipients(
  workflowId: string,
  recipients: Recipient[],
  invalidCount: number,
): void {
  recipientsByWorkflow.set(workflowId, recipients);
  invalidCountByWorkflow.set(workflowId, invalidCount);
}

export function resetRecipientCounts(workflowId: string): void {
  recipientsByWorkflow.delete(workflowId);
  invalidCountByWorkflow.delete(workflowId);
}
