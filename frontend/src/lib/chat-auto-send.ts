const autoSentKeys = new Set<string>();

export function hasAutoSentChatMessage(key: string): boolean {
  return autoSentKeys.has(key);
}

export function markAutoSentChatMessage(key: string): void {
  autoSentKeys.add(key);
}

export function autoSendKey(workflowId: string, userMessageId: string): string {
  return `${workflowId}:${userMessageId}`;
}
