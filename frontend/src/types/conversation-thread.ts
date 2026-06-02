export const CONVERSATION_MESSAGE_TYPES = [
  "agent_message",
  "prospect_reply",
  "agent_response",
] as const;

export type ConversationMessageType = (typeof CONVERSATION_MESSAGE_TYPES)[number];

export interface ConversationThreadMessage {
  id: string;
  type: ConversationMessageType;
  content: string;
}

export const conversationMessageLabels: Record<ConversationMessageType, string> = {
  agent_message: "Agent Message",
  prospect_reply: "Prospect Reply",
  agent_response: "Agent Response",
};
